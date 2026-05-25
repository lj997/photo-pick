"""
照片标签 CRUD API

提供照片标签的查询、手动添加、修改、删除，以及会话级标签统计。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.models import PhotoTag, Photo, gen_uuid
from app.models.database import get_db
from app.schemas import PhotoTagResponse, PhotoTagCreate, TagSummaryResponse, TagDimensionSummary, TagCount

router = APIRouter(prefix="/api", tags=["tags"])


@router.get("/photos/{photo_id}/tags", response_model=list[PhotoTagResponse])
async def get_photo_tags(photo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PhotoTag).where(PhotoTag.photo_id == photo_id).order_by(PhotoTag.dimension)
    )
    return result.scalars().all()


@router.post("/photos/{photo_id}/tags", response_model=PhotoTagResponse)
async def add_photo_tag(photo_id: str, body: PhotoTagCreate, db: AsyncSession = Depends(get_db)):
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    if body.dimension not in ("scene", "people", "setting", "composition"):
        raise HTTPException(status_code=400, detail="无效的标签维度")

    tag = PhotoTag(
        id=gen_uuid(),
        photo_id=photo_id,
        dimension=body.dimension,
        tag_value=body.tag_value.strip(),
        source="manual",
        confidence=None,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.put("/photos/{photo_id}/tags/{tag_id}", response_model=PhotoTagResponse)
async def update_photo_tag(photo_id: str, tag_id: str, body: PhotoTagCreate, db: AsyncSession = Depends(get_db)):
    tag = await db.get(PhotoTag, tag_id)
    if not tag or tag.photo_id != photo_id:
        raise HTTPException(status_code=404, detail="标签不存在")

    tag.dimension = body.dimension
    tag.tag_value = body.tag_value.strip()
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/photos/{photo_id}/tags/{tag_id}")
async def delete_photo_tag(photo_id: str, tag_id: str, db: AsyncSession = Depends(get_db)):
    tag = await db.get(PhotoTag, tag_id)
    if not tag or tag.photo_id != photo_id:
        raise HTTPException(status_code=404, detail="标签不存在")

    await db.delete(tag)
    await db.commit()
    return {"ok": True}


@router.get("/sessions/{session_id}/tags/summary", response_model=TagSummaryResponse)
async def get_tag_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PhotoTag.dimension, PhotoTag.tag_value, func.count(PhotoTag.id).label("cnt"))
        .join(Photo, Photo.id == PhotoTag.photo_id)
        .where(Photo.session_id == session_id)
        .group_by(PhotoTag.dimension, PhotoTag.tag_value)
        .order_by(PhotoTag.dimension, func.count(PhotoTag.id).desc())
    )
    rows = result.all()

    dims: dict[str, list[TagCount]] = {}
    for dimension, tag_value, cnt in rows:
        if dimension not in dims:
            dims[dimension] = []
        dims[dimension].append(TagCount(value=tag_value, count=cnt))

    dimensions = [
        TagDimensionSummary(dimension=d, tags=tags)
        for d, tags in dims.items()
    ]
    return TagSummaryResponse(dimensions=dimensions)
