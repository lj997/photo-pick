"""
缩略图生成服务

使用线程池并发生成小（300px）和大（1920px）两种 JPEG 缩略图。
自动修正 EXIF 方向信息。生成完成后通过 WebSocket 通知前端。
"""
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ExifTags
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Photo
from app.config import settings
from app.services.ws_manager import ws_manager

_executor = ThreadPoolExecutor(max_workers=settings.thumbnail_workers)


def _get_orientation(img: Image.Image) -> int:
    try:
        exif = img.getexif()
        for tag_id, value in exif.items():
            if ExifTags.TAGS.get(tag_id) == "Orientation":
                return value
    except Exception:
        pass
    return 1


def _apply_orientation(img: Image.Image) -> Image.Image:
    orientation = _get_orientation(img)
    if orientation == 2:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 3:
        img = img.rotate(180, expand=True)
    elif orientation == 4:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    elif orientation == 5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
    elif orientation == 6:
        img = img.rotate(270, expand=True)
    elif orientation == 7:
        img = img.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
    elif orientation == 8:
        img = img.rotate(90, expand=True)
    return img


def _generate_thumbnail(photo_id: str, filepath: str) -> tuple[bool, bool]:
    sm_path = settings.cache_dir / f"{photo_id}_sm.jpg"
    lg_path = settings.cache_dir / f"{photo_id}_lg.jpg"

    sm_ok = False
    lg_ok = False

    try:
        with Image.open(filepath) as img:
            img = _apply_orientation(img)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Generate large thumbnail
            lg_img = img.copy()
            lg_img.thumbnail((settings.thumbnail_lg_size, settings.thumbnail_lg_size), Image.LANCZOS)
            lg_img.save(str(lg_path), "JPEG", quality=settings.thumbnail_quality_lg)
            lg_ok = True

            # Generate small thumbnail from large
            sm_img = lg_img.copy()
            sm_img.thumbnail((settings.thumbnail_sm_size, settings.thumbnail_sm_size), Image.LANCZOS)
            sm_img.save(str(sm_path), "JPEG", quality=settings.thumbnail_quality_sm)
            sm_ok = True
    except Exception as e:
        print(f"Thumbnail generation failed for {filepath}: {e}")

    return sm_ok, lg_ok


async def generate_thumbnails_for_session(db: AsyncSession, session_id: str):
    result = await db.execute(
        select(Photo).where(
            Photo.session_id == session_id,
            Photo.thumb_sm_ready == False,
        )
    )
    photos = result.scalars().all()
    total = len(photos)
    loop = asyncio.get_event_loop()

    for idx, photo in enumerate(photos):
        if photo.format and photo.format.startswith("raw"):
            # Skip RAW for now, handled separately with rawpy
            continue

        sm_ok, lg_ok = await loop.run_in_executor(
            _executor, _generate_thumbnail, photo.id, photo.filepath
        )

        photo.thumb_sm_ready = sm_ok
        photo.thumb_lg_ready = lg_ok

        if sm_ok:
            await ws_manager.broadcast(session_id, "thumbnail_ready", {
                "photo_id": photo.id,
                "size": "sm",
            })

        if (idx + 1) % 10 == 0 or idx == total - 1:
            await db.commit()
            await ws_manager.broadcast(session_id, "thumbnail_progress", {
                "total": total,
                "processed": idx + 1,
            })

    await db.commit()


def get_thumbnail_path(photo_id: str, size: str) -> Path | None:
    suffix = "sm" if size == "sm" else "lg"
    path = settings.cache_dir / f"{photo_id}_{suffix}.jpg"
    if path.exists():
        return path
    return None
