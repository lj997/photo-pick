from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Group, GroupMember, Photo
from app.models.database import get_db
from app.schemas import GroupResponse, PhotoResponse
from app.services.grouping_service import detect_groups

router = APIRouter(prefix="/api", tags=["groups"])


@router.get("/sessions/{session_id}/groups")
async def list_groups(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Group).where(Group.session_id == session_id).order_by(Group.created_at)
    )
    groups = result.scalars().all()

    response = []
    for group in groups:
        count_result = await db.execute(
            select(func.count()).select_from(GroupMember).where(GroupMember.group_id == group.id)
        )
        count = count_result.scalar()
        response.append({
            "id": group.id,
            "session_id": group.session_id,
            "name": group.name,
            "group_type": group.group_type,
            "pick_photo_id": group.pick_photo_id,
            "member_count": count,
        })

    return response


@router.post("/sessions/{session_id}/groups/detect")
async def detect_groups_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    count = await detect_groups(db, session_id)
    return {"ok": True, "groups_created": count}


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


@router.delete("/groups/{group_id}")
async def delete_group(group_id: str, db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()
    return {"ok": True}
