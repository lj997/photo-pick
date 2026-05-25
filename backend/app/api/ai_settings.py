"""
AI 模型配置 API

提供 AI 视觉模型的配置读写和连接测试。
配置存储在数据库中，支持从前端 UI 动态修改无需重启。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import AISetting
from app.models.database import get_db
from app.schemas import AISettingsResponse, AISettingsUpdate

router = APIRouter(prefix="/api/ai-settings", tags=["ai-settings"])

SETTING_KEYS = ["ai_enabled", "ai_provider", "ai_model_name", "ai_api_key", "ai_base_url"]

DEFAULTS = {
    "ai_enabled": "false",
    "ai_provider": "claude",
    "ai_model_name": "claude-sonnet-4-20250514",
    "ai_api_key": "",
    "ai_base_url": "",
}


async def _get_all_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(AISetting).where(AISetting.key.in_(SETTING_KEYS)))
    rows = {r.key: r.value for r in result.scalars().all()}
    return {k: rows.get(k, DEFAULTS[k]) for k in SETTING_KEYS}


@router.get("", response_model=AISettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    raw = await _get_all_settings(db)
    return AISettingsResponse(
        ai_enabled=raw["ai_enabled"] == "true",
        ai_provider=raw["ai_provider"],
        ai_model_name=raw["ai_model_name"],
        ai_api_key=raw["ai_api_key"],
        ai_base_url=raw["ai_base_url"],
    )


@router.put("", response_model=AISettingsResponse)
async def update_settings(body: AISettingsUpdate, db: AsyncSession = Depends(get_db)):
    updates = {}
    if body.ai_enabled is not None:
        updates["ai_enabled"] = "true" if body.ai_enabled else "false"
    if body.ai_provider is not None:
        updates["ai_provider"] = body.ai_provider
    if body.ai_model_name is not None:
        updates["ai_model_name"] = body.ai_model_name
    if body.ai_api_key is not None:
        updates["ai_api_key"] = body.ai_api_key
    if body.ai_base_url is not None:
        updates["ai_base_url"] = body.ai_base_url

    for key, value in updates.items():
        existing = await db.get(AISetting, key)
        if existing:
            existing.value = value
        else:
            db.add(AISetting(key=key, value=value))

    await db.commit()
    return await get_settings(db)


@router.post("/test")
async def test_connection(db: AsyncSession = Depends(get_db)):
    from app.services.ai_provider import get_ai_provider

    raw = await _get_all_settings(db)
    try:
        provider = get_ai_provider(raw)
        result = await provider.test_connection()
        return {"ok": True, "message": result}
    except Exception as e:
        return {"ok": False, "message": str(e)}
