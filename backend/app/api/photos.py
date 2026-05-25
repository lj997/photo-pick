"""
照片列表与文件服务 API

提供照片分页查询（支持筛选排序）、缩略图和原图文件下载。
RAW 格式文件自动回退到大缩略图。
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Photo
from app.models.database import get_db
from app.schemas import PhotoResponse, PhotoListResponse
from app.services.thumbnail_service import get_thumbnail_path

router = APIRouter(prefix="/api", tags=["photos"])


@router.get("/sessions/{session_id}/photos", response_model=PhotoListResponse)
async def list_photos(
    session_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sort: str = Query("sort_order"),
    stars_min: int | None = None,
    stars_max: int | None = None,
    status: str | None = None,
    color_label: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Photo).where(Photo.session_id == session_id)

    if stars_min is not None:
        query = query.where(Photo.stars >= stars_min)
    if stars_max is not None:
        query = query.where(Photo.stars <= stars_max)
    if status:
        statuses = status.split(",")
        query = query.where(Photo.status.in_(statuses))
    if color_label:
        labels = color_label.split(",")
        query = query.where(Photo.color_label.in_(labels))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    sort_col = getattr(Photo, sort, Photo.sort_order)
    query = query.order_by(sort_col).offset(offset).limit(limit)

    result = await db.execute(query)
    photos = result.scalars().all()

    return PhotoListResponse(total=total, photos=photos)


@router.get("/photos/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: str, db: AsyncSession = Depends(get_db)):
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.get("/photos/{photo_id}/thumbnail/{size}")
async def get_thumbnail(photo_id: str, size: str, db: AsyncSession = Depends(get_db)):
    if size not in ("sm", "lg"):
        raise HTTPException(status_code=400, detail="Size must be 'sm' or 'lg'")

    path = get_thumbnail_path(photo_id, size)
    if not path:
        raise HTTPException(status_code=404, detail="Thumbnail not ready")

    return FileResponse(
        str(path),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/photos/{photo_id}/full")
async def get_full_photo(photo_id: str, db: AsyncSession = Depends(get_db)):
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = Path(photo.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Original file not found")

    ext = filepath.suffix.lower()
    raw_extensions = {".cr2", ".cr3", ".nef", ".arw", ".raf", ".rw2", ".dng", ".orf", ".pef"}

    # RAW files can't be rendered by browsers, serve the large thumbnail instead
    if ext in raw_extensions:
        thumb_path = get_thumbnail_path(photo_id, "lg")
        if thumb_path:
            return FileResponse(
                str(thumb_path),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        raise HTTPException(status_code=404, detail="RAW preview not ready")

    media_type = "image/jpeg"
    if ext in (".png",):
        media_type = "image/png"
    elif ext in (".tiff", ".tif"):
        media_type = "image/tiff"
    elif ext in (".webp",):
        media_type = "image/webp"
    elif ext in (".bmp",):
        media_type = "image/bmp"

    return FileResponse(
        str(filepath),
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )
