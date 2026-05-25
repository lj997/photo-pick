"""
会话管理 API

提供选片会话的创建（导入文件夹）、列表、详情、删除接口。
创建会话时自动触发后台缩略图生成任务。
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Session
from app.models.database import get_db
from app.schemas import SessionCreate, SessionResponse
from app.services.import_service import import_folder
from app.services.thumbnail_service import generate_thumbnails_for_session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    body: SessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await import_folder(db, body.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(_generate_thumbs_bg, session.id)
    return session


async def _generate_thumbs_bg(session_id: str):
    from app.models.database import async_session_factory
    async with async_session_factory() as db:
        await generate_thumbnails_for_session(db, session_id)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"ok": True}
