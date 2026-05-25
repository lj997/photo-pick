"""
评分标记 API

提供单张和批量更新照片的星级、颜色标签、入选/淘汰状态。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Photo
from app.models.database import get_db
from app.schemas import MarkUpdate, BatchMarkUpdate, PhotoResponse

router = APIRouter(prefix="/api", tags=["marks"])


@router.patch("/photos/{photo_id}/marks", response_model=PhotoResponse)
async def update_marks(
    photo_id: str,
    marks: MarkUpdate,
    db: AsyncSession = Depends(get_db),
):
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if marks.stars is not None:
        if not 0 <= marks.stars <= 5:
            raise HTTPException(status_code=400, detail="Stars must be 0-5")
        photo.stars = marks.stars
    if marks.color_label is not None:
        if marks.color_label not in ("", "red", "yellow", "green", "blue", "purple"):
            raise HTTPException(status_code=400, detail="Invalid color label")
        photo.color_label = marks.color_label if marks.color_label else None
    if marks.status is not None:
        if marks.status not in ("pending", "accepted", "rejected"):
            raise HTTPException(status_code=400, detail="Invalid status")
        photo.status = marks.status

    await db.commit()
    await db.refresh(photo)
    return photo


@router.patch("/photos/batch/marks")
async def batch_update_marks(
    body: BatchMarkUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Photo).where(Photo.id.in_(body.photo_ids))
    )
    photos = result.scalars().all()

    for photo in photos:
        if body.marks.stars is not None:
            photo.stars = body.marks.stars
        if body.marks.color_label is not None:
            photo.color_label = body.marks.color_label if body.marks.color_label else None
        if body.marks.status is not None:
            photo.status = body.marks.status

    await db.commit()
    return {"ok": True, "updated": len(photos)}
