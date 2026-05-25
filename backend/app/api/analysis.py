from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Photo, AnalysisResult
from app.models.database import get_db, async_session_factory
from app.schemas import AnalysisResultResponse
from app.services.ws_manager import ws_manager

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/sessions/{session_id}/analyze")
async def start_analysis(
    session_id: str,
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    types = body.get("types", ["blur", "exposure"])

    if "content_tags" in types:
        background_tasks.add_task(_run_content_analysis, session_id)
        types = [t for t in types if t != "content_tags"]

    if types:
        background_tasks.add_task(_run_analysis, session_id, types)

    return {"ok": True, "types": body.get("types", ["blur", "exposure"])}


async def _run_content_analysis(session_id: str):
    from app.services.content_tag_service import analyze_session_content

    async with async_session_factory() as db:
        await analyze_session_content(db, session_id)


async def _run_analysis(session_id: str, types: list[str]):
    from app.analysis.blur_detector import detect_blur
    from app.analysis.exposure_analyzer import analyze_exposure

    async with async_session_factory() as db:
        result = await db.execute(
            select(Photo).where(Photo.session_id == session_id)
        )
        photos = result.scalars().all()

        for idx, photo in enumerate(photos):
            if "blur" in types:
                score, is_issue = detect_blur(photo.filepath)
                await _save_result(db, photo.id, "blur", score, is_issue)

            if "exposure" in types:
                score, is_issue, data = analyze_exposure(photo.filepath)
                await _save_result(db, photo.id, "exposure", score, is_issue, data)

            await ws_manager.broadcast(session_id, "analysis_complete", {
                "photo_id": photo.id,
                "processed": idx + 1,
                "total": len(photos),
            })

        await db.commit()


async def _save_result(
    db: AsyncSession,
    photo_id: str,
    analysis_type: str,
    score: float,
    is_issue: bool,
    result_data: str | None = None,
):
    from app.models import gen_uuid

    # Remove old result of same type
    existing = await db.execute(
        select(AnalysisResult).where(
            AnalysisResult.photo_id == photo_id,
            AnalysisResult.analysis_type == analysis_type,
        )
    )
    for old in existing.scalars().all():
        await db.delete(old)

    ar = AnalysisResult(
        id=gen_uuid(),
        photo_id=photo_id,
        analysis_type=analysis_type,
        score=score,
        is_issue=is_issue,
        result_data=result_data,
    )
    db.add(ar)


@router.get("/photos/{photo_id}/analysis", response_model=list[AnalysisResultResponse])
async def get_analysis_results(photo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.photo_id == photo_id)
    )
    return result.scalars().all()
