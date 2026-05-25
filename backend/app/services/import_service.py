"""
照片导入服务

递归扫描指定文件夹中的图片文件（含 RAW 格式），提取 EXIF 元数据，
创建 Photo 记录并写入数据库。通过 WebSocket 推送导入进度。
"""
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import exifread
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Photo, Session, gen_uuid
from app.config import settings
from app.services.ws_manager import ws_manager

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp",
    ".cr2", ".cr3", ".nef", ".arw", ".raf", ".rw2", ".dng", ".orf", ".pef",
}


def _extract_exif(filepath: str) -> dict:
    result = {}
    try:
        with open(filepath, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal", details=False)

        if "EXIF DateTimeOriginal" in tags:
            dt_str = str(tags["EXIF DateTimeOriginal"])
            try:
                result["taken_at"] = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass

        if "Image Make" in tags:
            result["camera_make"] = str(tags["Image Make"]).strip()
        if "Image Model" in tags:
            result["camera_model"] = str(tags["Image Model"]).strip()
        if "EXIF LensModel" in tags:
            result["lens"] = str(tags["EXIF LensModel"]).strip()
        if "EXIF FocalLength" in tags:
            val = tags["EXIF FocalLength"]
            try:
                result["focal_length"] = float(val.values[0].num) / float(val.values[0].den)
            except (AttributeError, ZeroDivisionError, IndexError):
                pass
        if "EXIF FNumber" in tags:
            val = tags["EXIF FNumber"]
            try:
                result["aperture"] = float(val.values[0].num) / float(val.values[0].den)
            except (AttributeError, ZeroDivisionError, IndexError):
                pass
        if "EXIF ExposureTime" in tags:
            result["shutter_speed"] = str(tags["EXIF ExposureTime"])
        if "EXIF ISOSpeedRatings" in tags:
            try:
                result["iso"] = int(str(tags["EXIF ISOSpeedRatings"]))
            except ValueError:
                pass
    except Exception:
        pass
    return result


def _get_image_dimensions(filepath: str) -> tuple[int | None, int | None]:
    try:
        with Image.open(filepath) as img:
            return img.width, img.height
    except Exception:
        return None, None


async def import_folder(db: AsyncSession, folder_path: str) -> Session:
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Folder does not exist: {folder_path}")

    session = Session(
        id=gen_uuid(),
        name=path.name,
        folder_path=str(path.resolve()),
    )
    db.add(session)

    image_files = sorted(
        [f for f in path.rglob("*") if f.suffix.lower() in IMAGE_EXTENSIONS and f.is_file()],
        key=lambda f: f.name,
    )

    total = len(image_files)
    photos = []

    for idx, file_path in enumerate(image_files):
        ext = file_path.suffix.lower()
        fmt = "raw" if ext in {".cr2", ".cr3", ".nef", ".arw", ".raf", ".rw2", ".dng", ".orf", ".pef"} else ext.lstrip(".")

        exif = _extract_exif(str(file_path))
        width, height = _get_image_dimensions(str(file_path)) if fmt != "raw" else (None, None)

        photo = Photo(
            id=gen_uuid(),
            session_id=session.id,
            filename=file_path.name,
            filepath=str(file_path.resolve()),
            file_size=file_path.stat().st_size,
            width=width,
            height=height,
            format=fmt,
            sort_order=idx,
            **exif,
        )
        photos.append(photo)
        db.add(photo)

        if (idx + 1) % 50 == 0 or idx == total - 1:
            await ws_manager.broadcast(session.id, "import_progress", {
                "total": total,
                "processed": idx + 1,
                "current_file": file_path.name,
            })

    session.photo_count = total
    await db.commit()
    await db.refresh(session)
    return session
