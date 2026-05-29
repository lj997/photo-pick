"""
照片标签 CRUD API

提供照片标签的查询、手动添加、修改、删除，以及会话级标签统计。
包含无需云端 AI 的本地规则标签生成，用于整理场景/人物/地点等维度。
"""
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from PIL import Image, ImageStat

from app.models import PhotoTag, Photo, gen_uuid
from app.models.database import get_db
from app.schemas import (
    LocalTagAnalysisRequest,
    LocalTagAnalysisResponse,
    PhotoTagCreate,
    PhotoTagResponse,
    TagCount,
    TagDimensionSummary,
    TagSummaryResponse,
)
from app.services.thumbnail_service import get_thumbnail_path

router = APIRouter(prefix="/api", tags=["tags"])

GENERIC_PATH_PARTS = {
    "photos", "photo", "pictures", "picture", "images", "image", "dcim",
    "jpg", "jpeg", "raw", "edited", "export", "exports", "camera",
    "照片", "图片", "相片", "原图", "导入", "导出", "精选", "未分类",
}

KEYWORD_TAGS = {
    "婚礼": ("scene", "婚礼"), "wedding": ("scene", "婚礼"),
    "生日": ("scene", "生日"), "birthday": ("scene", "生日"),
    "旅行": ("scene", "旅行"), "travel": ("scene", "旅行"), "trip": ("scene", "旅行"),
    "毕业": ("scene", "毕业"), "舞台": ("scene", "舞台"), "演出": ("scene", "演出"),
    "美食": ("scene", "美食"), "food": ("scene", "美食"), "餐厅": ("scene", "美食"),
    "猫": ("scene", "宠物"), "狗": ("scene", "宠物"), "pet": ("scene", "宠物"),
    "人像": ("people", "人像"), "portrait": ("people", "人像"), "selfie": ("people", "自拍"),
    "合照": ("people", "合照"), "group": ("people", "合照"),
    "海": ("setting", "海边"), "海边": ("setting", "海边"), "beach": ("setting", "海边"),
    "山": ("setting", "山野"), "森林": ("setting", "森林"), "公园": ("setting", "公园"),
    "室内": ("setting", "室内"), "indoor": ("setting", "室内"),
    "户外": ("setting", "户外"), "outdoor": ("setting", "户外"),
    "夜": ("scene", "夜景"), "夜景": ("scene", "夜景"), "night": ("scene", "夜景"),
}


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


@router.post("/sessions/{session_id}/tags/local", response_model=LocalTagAnalysisResponse)
async def generate_local_tags(
    session_id: str,
    body: LocalTagAnalysisRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    mode = (body.mode if body else "vision").lower()
    if mode not in ("rules", "vision"):
        raise HTTPException(status_code=400, detail="mode must be rules or vision")

    result = await db.execute(select(Photo).where(Photo.session_id == session_id).order_by(Photo.sort_order))
    photos = list(result.scalars().all())
    if not photos:
        return LocalTagAnalysisResponse(total=0, tagged=0, tags_created=0, mode=mode)

    photo_id_query = select(Photo.id).where(Photo.session_id == session_id)
    await db.execute(
        delete(PhotoTag).where(
            PhotoTag.photo_id.in_(photo_id_query),
            PhotoTag.source == "local",
        )
    )

    existing_result = await db.execute(
        select(PhotoTag.photo_id, PhotoTag.dimension, PhotoTag.tag_value).where(
            PhotoTag.photo_id.in_(photo_id_query),
            PhotoTag.source != "local",
        )
    )
    existing = {(pid, dim, val) for pid, dim, val in existing_result.all()}

    tagged = 0
    tags_created = 0
    failed = 0
    for photo in photos:
        try:
            tags = _infer_local_tags(photo, include_vision=(mode == "vision"))
        except Exception:
            failed += 1
            tags = _infer_rule_tags(photo)

        created_for_photo = 0
        for dimension, value in sorted(tags):
            key = (photo.id, dimension, value)
            if key in existing:
                continue
            db.add(PhotoTag(
                id=gen_uuid(),
                photo_id=photo.id,
                dimension=dimension,
                tag_value=value,
                source="local",
                confidence=0.55,
            ))
            tags_created += 1
            created_for_photo += 1
        if created_for_photo > 0:
            tagged += 1

    await db.commit()
    return LocalTagAnalysisResponse(total=len(photos), tagged=tagged, tags_created=tags_created, mode=mode, failed=failed)


def _infer_local_tags(photo: Photo, include_vision: bool = True) -> set[tuple[str, str]]:
    tags = _infer_rule_tags(photo)
    if include_vision:
        tags.update(_infer_image_tags(photo))
    return tags


def _infer_rule_tags(photo: Photo) -> set[tuple[str, str]]:
    tags: set[tuple[str, str]] = set()
    path = Path(photo.filepath)
    text = " ".join([photo.filename, *path.parts[-5:]]).lower()

    for keyword, tag in KEYWORD_TAGS.items():
        if keyword.lower() in text:
            tags.add(tag)

    for part in path.parts[-4:-1]:
        cleaned = _clean_path_part(part)
        if cleaned:
            tags.add(("setting", cleaned))

    if photo.taken_at:
        hour = photo.taken_at.hour
        if 5 <= hour < 8:
            tags.add(("scene", "清晨"))
        elif 17 <= hour < 20:
            tags.add(("scene", "黄昏"))
        elif hour >= 20 or hour < 5:
            tags.add(("scene", "夜景"))

    if photo.width and photo.height:
        ratio = photo.width / max(photo.height, 1)
        if ratio > 1.25:
            tags.add(("composition", "横构图"))
        elif ratio < 0.8:
            tags.add(("composition", "竖构图"))
        else:
            tags.add(("composition", "方构图"))

    if photo.focal_length:
        if photo.focal_length >= 70:
            tags.add(("composition", "长焦"))
        elif photo.focal_length <= 24:
            tags.add(("composition", "广角"))

    return tags


def _clean_path_part(value: str) -> str | None:
    cleaned = re.sub(r"^\d{4}[-_.]?\d{0,4}", "", value).strip(" -_.")
    if not cleaned or cleaned.lower() in GENERIC_PATH_PARTS:
        return None
    if re.fullmatch(r"\d+", cleaned):
        return None
    return cleaned[:24]


def _infer_image_tags(photo: Photo) -> set[tuple[str, str]]:
    image_path = get_thumbnail_path(photo.id, "lg")
    if not image_path:
        path = Path(photo.filepath)
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
            return set()
        image_path = path

    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((320, 320))
            stat = ImageStat.Stat(img)
            mean_r, mean_g, mean_b = stat.mean
            brightness = sum(stat.mean) / 3
            tags: set[tuple[str, str]] = set()

            if brightness < 55:
                tags.add(("scene", "暗光"))
                tags.add(("scene", "夜景"))
            elif brightness > 205:
                tags.add(("scene", "明亮"))

            if mean_g > mean_r * 1.12 and mean_g > mean_b * 1.12:
                tags.add(("setting", "自然"))
                tags.add(("setting", "绿植"))
            if mean_b > mean_r * 1.15 and mean_b > mean_g * 1.05:
                tags.add(("setting", "天空/水面"))
                tags.add(("setting", "户外"))
            if mean_r > mean_b * 1.18 and mean_g > mean_b * 1.05:
                tags.add(("setting", "暖色环境"))

            face_count = _detect_faces(img)
            if face_count > 0:
                tags.add(("people", f"{face_count}人"))
                tags.add(("scene", "人物"))
                tags.add(("people", "人像" if face_count == 1 else "合照"))

            return tags
    except Exception:
        return set()


def _detect_faces(img: Image.Image) -> int:
    try:
        import cv2
        import numpy as np

        arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(str(cascade_path))
        if detector.empty():
            return 0
        faces = detector.detectMultiScale(arr, scaleFactor=1.1, minNeighbors=5, minSize=(28, 28))
        return min(len(faces), 10)
    except Exception:
        return 0
