from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Group, GroupMember, Photo
from app.models.database import get_db, async_session_factory
from app.schemas import GroupResponse, PhotoResponse
from app.services.grouping_service import detect_groups
from app.services.content_grouping_service import detect_content_groups
from app.services.ws_manager import ws_manager

router = APIRouter(prefix="/api", tags=["groups"])


@router.get("/sessions/{session_id}/groups")
async def list_groups(
    session_id: str,
    group_type: str | None = None,
    include_members: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(Group).where(Group.session_id == session_id)
    if group_type:
        query = query.where(Group.group_type == group_type)
    query = query.order_by(Group.created_at)

    result = await db.execute(query)
    groups = result.scalars().all()

    response = []
    for group in groups:
        count_result = await db.execute(
            select(func.count()).select_from(GroupMember).where(GroupMember.group_id == group.id)
        )
        count = count_result.scalar()

        item = {
            "id": group.id,
            "session_id": group.session_id,
            "name": group.name,
            "group_type": group.group_type,
            "pick_photo_id": group.pick_photo_id,
            "member_count": count,
        }

        if include_members:
            members_result = await db.execute(
                select(Photo)
                .join(GroupMember, GroupMember.photo_id == Photo.id)
                .where(GroupMember.group_id == group.id)
                .order_by(GroupMember.position)
            )
            item["members"] = members_result.scalars().all()

        response.append(item)

    return response


@router.post("/sessions/{session_id}/groups/detect")
async def detect_groups_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    count = await detect_groups(db, session_id)
    return {"ok": True, "groups_created": count}


@router.post("/sessions/{session_id}/groups/detect-content")
async def detect_content_groups_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    count = await detect_content_groups(db, session_id)
    return {"ok": True, "groups_created": count}


@router.post("/sessions/{session_id}/groups/detect-similar")
async def detect_similar_groups_endpoint(
    session_id: str,
    background_tasks: BackgroundTasks,
    threshold: int | None = None,
):
    background_tasks.add_task(_run_similarity_detection, session_id, threshold)
    return {"ok": True, "message": "相似度检测已启动"}


async def _run_similarity_detection(session_id: str, threshold: int | None = None):
    from app.services.similarity_service import compute_hashes, detect_similar_groups
    async with async_session_factory() as db:
        await compute_hashes(db, session_id)
        group_count = await detect_similar_groups(db, session_id, threshold=threshold)
        await ws_manager.broadcast(session_id, "similarity_complete", {
            "groups_created": group_count,
        })


@router.get("/groups/{group_id}")
async def get_group(group_id: str, db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members_result = await db.execute(
        select(Photo)
        .join(GroupMember, GroupMember.photo_id == Photo.id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.position)
    )
    members = members_result.scalars().all()

    return {
        "id": group.id,
        "session_id": group.session_id,
        "name": group.name,
        "group_type": group.group_type,
        "pick_photo_id": group.pick_photo_id,
        "member_count": len(members),
        "members": members,
    }


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if "name" in body:
        group.name = body["name"]
    if "pick_photo_id" in body:
        group.pick_photo_id = body["pick_photo_id"]

    await db.commit()
    return {"ok": True}


@router.post("/groups/{group_id}/reset")
async def reset_group_pk(group_id: str, db: AsyncSession = Depends(get_db)):
    """重置分组的 PK 结果：将所有成员状态恢复为 pending，清除 pick_photo_id"""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.pick_photo_id = None

    members_result = await db.execute(
        select(Photo)
        .join(GroupMember, GroupMember.photo_id == Photo.id)
        .where(GroupMember.group_id == group_id)
    )
    for photo in members_result.scalars().all():
        photo.status = "pending"

    await db.commit()
    return {"ok": True}


@router.delete("/groups/{group_id}")
async def delete_group(group_id: str, db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()
    return {"ok": True}
