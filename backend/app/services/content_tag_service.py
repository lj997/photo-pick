"""
内容标签提取服务

调用 AI 视觉模型分析照片内容，提取结构化标签并存入数据库。
支持批量分析整个会话的照片，通过 WebSocket 推送进度。
"""
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import Photo, PhotoTag, AISetting, AnalysisResult, gen_uuid
from app.services.ai_provider import get_ai_provider
from app.services.thumbnail_service import get_thumbnail_path
from app.services.ws_manager import ws_manager


async def _load_ai_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(AISetting))
    rows = {r.key: r.value for r in result.scalars().all()}
    defaults = {
        "ai_enabled": "false",
        "ai_provider": "claude",
        "ai_model_name": "claude-sonnet-4-20250514",
        "ai_api_key": "",
        "ai_base_url": "",
    }
    return {k: rows.get(k, v) for k, v in defaults.items()}


def _normalize_tags(ai_result: dict) -> list[dict]:
    """将 AI 返回的 JSON 转换为标准化标签列表"""
    tags = []

    for scene in ai_result.get("scene", []):
        if scene:
            tags.append({"dimension": "scene", "tag_value": scene})

    people = ai_result.get("people", {})
    if isinstance(people, dict):
        count = people.get("count", 0)
        if count > 0:
            tags.append({"dimension": "people", "tag_value": f"{count}人"})
        for t in people.get("tags", []):
            if t:
                tags.append({"dimension": "people", "tag_value": t})
    elif isinstance(people, list):
        for t in people:
            if t:
                tags.append({"dimension": "people", "tag_value": t})

    for setting in ai_result.get("setting", []):
        if setting:
            tags.append({"dimension": "setting", "tag_value": setting})

    for comp in ai_result.get("composition", []):
        if comp:
            tags.append({"dimension": "composition", "tag_value": comp})

    return tags


async def analyze_photo_content(db: AsyncSession, photo: Photo, settings: dict[str, str]) -> bool:
    """分析单张照片内容，返回是否成功"""
    # 使用大缩略图
    thumb_path = get_thumbnail_path(photo.id, "lg")
    if not thumb_path:
        return False

    provider = get_ai_provider(settings)

    try:
        ai_result = await provider.analyze_image(str(thumb_path))
    except Exception as e:
        # 记录失败
        await _save_analysis_result(db, photo.id, None, str(e))
        return False

    # 保存原始 AI 响应到 AnalysisResult
    await _save_analysis_result(db, photo.id, ai_result, None)

    # 删除旧的 AI 标签
    await db.execute(
        delete(PhotoTag).where(
            PhotoTag.photo_id == photo.id,
            PhotoTag.source == "ai",
        )
    )

    # 写入标准化标签
    normalized = _normalize_tags(ai_result)
    for tag_data in normalized:
        tag = PhotoTag(
            id=gen_uuid(),
            photo_id=photo.id,
            dimension=tag_data["dimension"],
            tag_value=tag_data["tag_value"],
            source="ai",
            confidence=0.9,
        )
        db.add(tag)

    return True


async def _save_analysis_result(db: AsyncSession, photo_id: str, result: dict | None, error: str | None):
    """保存分析结果到 AnalysisResult 表"""
    # 删除旧结果
    old = await db.execute(
        select(AnalysisResult).where(
            AnalysisResult.photo_id == photo_id,
            AnalysisResult.analysis_type == "content_tags",
        )
    )
    for r in old.scalars().all():
        await db.delete(r)

    ar = AnalysisResult(
        id=gen_uuid(),
        photo_id=photo_id,
        analysis_type="content_tags",
        score=1.0 if result else 0.0,
        result_data=json.dumps(result, ensure_ascii=False) if result else error,
        is_issue=result is None,
    )
    db.add(ar)


async def analyze_session_content(db: AsyncSession, session_id: str):
    """批量分析会话中所有照片的内容标签"""
    settings = await _load_ai_settings(db)

    if settings.get("ai_enabled") != "true":
        await ws_manager.broadcast(session_id, "content_tags_error", {"message": "AI 功能未启用"})
        return

    result = await db.execute(
        select(Photo).where(
            Photo.session_id == session_id,
            Photo.thumb_lg_ready == True,
        ).order_by(Photo.sort_order)
    )
    photos = result.scalars().all()
    total = len(photos)

    if total == 0:
        return

    await ws_manager.broadcast(session_id, "content_tags_progress", {
        "total": total, "processed": 0, "status": "started"
    })

    for idx, photo in enumerate(photos):
        success = await analyze_photo_content(db, photo, settings)

        if (idx + 1) % 3 == 0 or idx == total - 1:
            await db.commit()

        await ws_manager.broadcast(session_id, "content_tags_progress", {
            "total": total,
            "processed": idx + 1,
            "current_file": photo.filename,
            "success": success,
        })

    await db.commit()
    await ws_manager.broadcast(session_id, "content_tags_progress", {
        "total": total, "processed": total, "status": "completed"
    })
