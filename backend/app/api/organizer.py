"""
照片整理 API

根据照片元数据和内容标签生成整理方案，并将照片复制或移动到目标目录。
同时提供 Markdown 笔记读写，方便在整理后的目录里记录照片故事。
"""
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Photo, PhotoTag
from app.models.database import get_db
from app.schemas import (
    NoteReadResponse,
    NoteSaveRequest,
    NoteSaveResponse,
    OrganizeConfig,
    OrganizeGroupPreview,
    OrganizePhotoPreview,
    OrganizePreviewResponse,
    OrganizeResultResponse,
)

router = APIRouter(prefix="/api", tags=["organizer"])

SAFE_NOTE_RE = re.compile(r"^[\w\-. \u4e00-\u9fff]+\.md$", re.IGNORECASE)


@router.post("/sessions/{session_id}/organizer/preview", response_model=OrganizePreviewResponse)
async def preview_organize(
    session_id: str,
    config: OrganizeConfig,
    db: AsyncSession = Depends(get_db),
):
    photos = await _load_photos(session_id, config, db)
    tag_map = await _load_tag_map([p.id for p in photos], db)
    buckets: dict[str, list[Photo]] = defaultdict(list)

    for photo in photos:
        buckets[_target_path(photo, config, tag_map)].append(photo)

    groups = [
        OrganizeGroupPreview(
            path=path or ".",
            count=len(items),
            sample_filenames=[p.filename for p in items[:4]],
            photos=[_photo_preview(p, path or ".", tag_map) for p in items],
        )
        for path, items in sorted(buckets.items(), key=lambda item: item[0])
    ]

    return OrganizePreviewResponse(
        total=len(photos),
        destination=str(Path(config.destination)),
        groups=groups,
    )


@router.post("/sessions/{session_id}/organizer/apply", response_model=OrganizeResultResponse)
async def apply_organize(
    session_id: str,
    config: OrganizeConfig,
    db: AsyncSession = Depends(get_db),
):
    if config.mode not in ("copy", "move"):
        raise HTTPException(status_code=400, detail="mode must be copy or move")

    photos = await _load_photos(session_id, config, db)
    if not photos:
        raise HTTPException(status_code=400, detail="没有符合条件的照片")

    tag_map = await _load_tag_map([p.id for p in photos], db)
    base_dest = Path(config.destination).expanduser()
    base_dest.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    for idx, photo in enumerate(photos):
        src = Path(photo.filepath)
        if not src.exists():
            skipped += 1
            continue

        subfolder = _target_path(photo, config, tag_map)
        dest_dir = base_dest / subfolder if subfolder else base_dest
        dest_dir.mkdir(parents=True, exist_ok=True)

        filename = _apply_rename_template(config.rename_template, photo, idx) if config.rename_template else photo.filename
        dst = _dedupe_path(dest_dir / _safe_filename(filename))

        if config.mode == "move":
            shutil.move(str(src), str(dst))
            photo.filepath = str(dst)
        else:
            shutil.copy2(str(src), str(dst))
        processed += 1

    note_path: Path | None = None
    if config.include_note_template:
        note_path = base_dest / "PHOTO_STORY.md"
        if not note_path.exists():
            note_path.write_text(_default_note_content(photos, processed, config), encoding="utf-8")

    await db.commit()

    return OrganizeResultResponse(
        total=len(photos),
        processed=processed,
        skipped=skipped,
        destination=str(base_dest),
        note_path=str(note_path) if note_path else None,
    )


@router.get("/organizer/note", response_model=NoteReadResponse)
async def read_note(
    directory: str = Query(...),
    filename: str = Query("PHOTO_STORY.md"),
):
    note_path = _safe_note_path(directory, filename)
    if not note_path.exists():
        return NoteReadResponse(path=str(note_path), exists=False, content="")
    return NoteReadResponse(path=str(note_path), exists=True, content=note_path.read_text(encoding="utf-8"))


@router.post("/organizer/note", response_model=NoteSaveResponse)
async def save_note(request: NoteSaveRequest):
    note_path = _safe_note_path(request.directory, request.filename)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(request.content, encoding="utf-8")
    return NoteSaveResponse(path=str(note_path))


async def _load_photos(session_id: str, config: OrganizeConfig, db: AsyncSession) -> list[Photo]:
    query = select(Photo).where(Photo.session_id == session_id)
    filters = config.filters
    if filters:
        if filters.stars_min is not None:
            query = query.where(Photo.stars >= filters.stars_min)
        if filters.status:
            query = query.where(Photo.status.in_(filters.status))
        if filters.colors:
            query = query.where(Photo.color_label.in_(filters.colors))
        if filters.tag:
            parts = filters.tag.split(":", 1)
            if len(parts) == 2:
                dim, val = parts
                query = query.where(
                    Photo.id.in_(
                        select(PhotoTag.photo_id).where(
                            PhotoTag.dimension == dim,
                            PhotoTag.tag_value == val,
                        )
                    )
                )
    result = await db.execute(query.order_by(Photo.taken_at, Photo.sort_order))
    return list(result.scalars().all())


async def _load_tag_map(photo_ids: list[str], db: AsyncSession) -> dict[str, dict[str, list[str]]]:
    if not photo_ids:
        return {}
    result = await db.execute(select(PhotoTag).where(PhotoTag.photo_id.in_(photo_ids)))
    tag_map: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for tag in result.scalars().all():
        tag_map[tag.photo_id][tag.dimension].append(tag.tag_value)
    return tag_map


def _group_path(photo: Photo, group_by: list[str], tag_map: dict[str, dict[str, list[str]]]) -> str:
    parts: list[str] = []
    for key in group_by:
        value = _group_value(photo, key, tag_map)
        if value:
            parts.append(_safe_segment(value))
    return "/".join(parts)


def _target_path(photo: Photo, config: OrganizeConfig, tag_map: dict[str, dict[str, list[str]]]) -> str:
    manual = (config.manual_paths or {}).get(photo.id)
    if manual is not None:
        return _safe_relative_path(manual)
    return _group_path(photo, config.group_by, tag_map)


def _photo_preview(photo: Photo, target_path: str, tag_map: dict[str, dict[str, list[str]]]) -> OrganizePhotoPreview:
    tags = [
        f"{dimension}:{value}"
        for dimension, values in tag_map.get(photo.id, {}).items()
        for value in values[:3]
    ]
    return OrganizePhotoPreview(
        id=photo.id,
        filename=photo.filename,
        target_path=target_path,
        taken_at=photo.taken_at,
        camera_model=photo.camera_model,
        lens=photo.lens,
        format=photo.format,
        file_size=photo.file_size,
        stars=photo.stars,
        color_label=photo.color_label,
        status=photo.status,
        tags=tags[:8],
    )


def _group_value(photo: Photo, key: str, tag_map: dict[str, dict[str, list[str]]]) -> str:
    taken = photo.taken_at or photo.created_at or datetime.utcnow()
    if key == "year":
        return taken.strftime("%Y")
    if key == "month":
        return taken.strftime("%Y-%m")
    if key == "date":
        return taken.strftime("%Y-%m-%d")
    if key == "status":
        return {"accepted": "入选", "rejected": "淘汰", "pending": "待定"}.get(photo.status, photo.status or "待定")
    if key == "stars":
        return f"{photo.stars}星" if photo.stars else "未评分"
    if key == "color":
        return photo.color_label or "无色标"
    if key == "camera":
        return photo.camera_model or photo.camera_make or "未知相机"
    if key == "lens":
        return photo.lens or "未知镜头"
    if key == "format":
        return (photo.format or Path(photo.filename).suffix.lstrip(".") or "unknown").lower()
    if key.startswith("tag:"):
        dimension = key.split(":", 1)[1]
        values = tag_map.get(photo.id, {}).get(dimension, [])
        if not values:
            labels = {"scene": "内容场景", "people": "人物", "setting": "地点环境", "composition": "构图"}
            return f"未标记{labels.get(dimension, dimension)}"
        return "+".join(_safe_segment(v) for v in values[:3])
    return ""


def _safe_segment(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(value)).strip()
    return cleaned[:80] or "未分类"


def _safe_relative_path(value: str) -> str:
    parts = []
    for raw in re.split(r"[\\/]+", value.strip()):
        if raw in ("", ".", ".."):
            continue
        parts.append(_safe_segment(raw))
    return "/".join(parts)


def _safe_filename(value: str) -> str:
    path = Path(value)
    return _safe_segment(path.stem) + path.suffix


def _dedupe_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while path.exists():
        path = path.with_name(f"{stem}_{counter}{suffix}")
        counter += 1
    return path


def _apply_rename_template(template: str | None, photo: Photo, idx: int) -> str:
    ext = Path(photo.filename).suffix
    taken = photo.taken_at or photo.created_at or datetime.utcnow()
    name = (template or "{original}").format(
        date=taken.strftime("%Y%m%d"),
        time=taken.strftime("%H%M%S"),
        year=taken.strftime("%Y"),
        month=taken.strftime("%m"),
        day=taken.strftime("%d"),
        seq=str(idx + 1).zfill(4),
        original=Path(photo.filename).stem,
        camera=photo.camera_model or "unknown",
        stars=photo.stars,
        status=photo.status,
    )
    return name + ext


def _safe_note_path(directory: str, filename: str) -> Path:
    if not SAFE_NOTE_RE.match(filename):
        raise HTTPException(status_code=400, detail="笔记文件名必须是安全的 .md 文件名")
    base = Path(directory).expanduser()
    return base / filename


def _default_note_content(photos: list[Photo], processed: int, config: OrganizeConfig) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        "# 照片故事\n\n"
        f"> 整理时间：{now}  \n"
        f"> 整理数量：{processed} / {len(photos)}  \n"
        f"> 整理方式：{'移动' if config.mode == 'move' else '复制'}  \n\n"
        "## 这组照片记录了什么\n\n"
        "- \n\n"
        "## 值得记住的瞬间\n\n"
        "- \n\n"
        "## 人物、地点与细节\n\n"
        "- \n"
    )
