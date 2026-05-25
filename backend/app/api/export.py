"""
导出 API

启动后台导出任务，将筛选后的照片复制/移动到目标文件夹。
支持子文件夹分组、文件重命名模板、冲突自动编号。
通过 WebSocket 实时推送导出进度。
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Photo, ExportJob, gen_uuid
from app.models.database import get_db, async_session_factory
from app.schemas import ExportConfig, ExportJobResponse
from app.services.ws_manager import ws_manager

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/sessions/{session_id}/export", response_model=ExportJobResponse)
async def start_export(
    session_id: str,
    config: ExportConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    query = select(Photo).where(Photo.session_id == session_id)

    if config.filter_stars_min is not None:
        query = query.where(Photo.stars >= config.filter_stars_min)
    if config.filter_status:
        query = query.where(Photo.status.in_(config.filter_status))
    if config.filter_colors:
        query = query.where(Photo.color_label.in_(config.filter_colors))

    result = await db.execute(query.order_by(Photo.sort_order))
    photos = result.scalars().all()

    if not photos:
        raise HTTPException(status_code=400, detail="No photos match the filter criteria")

    job = ExportJob(
        id=gen_uuid(),
        session_id=session_id,
        config=json.dumps(config.model_dump()),
        status="pending",
        total_count=len(photos),
        processed_count=0,
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(_run_export, job.id, [p.id for p in photos], config, session_id)
    return job


def _get_subfolder(photo, group_by: str | None) -> str:
    if not group_by:
        return ""
    if group_by == "status":
        return photo.status or "pending"
    elif group_by == "color":
        return photo.color_label or "no_label"
    elif group_by == "stars":
        return f"{photo.stars}_stars"
    return ""


async def _run_export(job_id: str, photo_ids: list[str], config: ExportConfig, session_id: str):
    async with async_session_factory() as db:
        job = await db.get(ExportJob, job_id)
        job.status = "running"
        job.started_at = datetime.utcnow()
        await db.commit()

        base_dest = Path(config.destination)
        base_dest.mkdir(parents=True, exist_ok=True)

        for idx, photo_id in enumerate(photo_ids):
            photo = await db.get(Photo, photo_id)
            if not photo:
                continue

            src = Path(photo.filepath)
            if not src.exists():
                continue

            # Determine destination subfolder
            subfolder = _get_subfolder(photo, config.group_by)
            if subfolder:
                dest = base_dest / subfolder
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest = base_dest

            # Determine filename
            if config.rename_template:
                new_name = _apply_rename_template(config.rename_template, photo, idx)
            else:
                new_name = photo.filename

            dst = dest / new_name
            # Avoid collision
            if dst.exists():
                stem = dst.stem
                suffix = dst.suffix
                counter = 1
                while dst.exists():
                    dst = dest / f"{stem}_{counter}{suffix}"
                    counter += 1

            if config.mode == "move":
                shutil.move(str(src), str(dst))
            else:
                shutil.copy2(str(src), str(dst))

            job.processed_count = idx + 1
            await db.commit()

            if (idx + 1) % 5 == 0 or idx == len(photo_ids) - 1:
                await ws_manager.broadcast(session_id, "export_progress", {
                    "job_id": job_id,
                    "total": job.total_count,
                    "exported": idx + 1,
                })

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        await db.commit()

        await ws_manager.broadcast(session_id, "export_progress", {
            "job_id": job_id,
            "total": job.total_count,
            "exported": job.total_count,
            "status": "completed",
        })


def _apply_rename_template(template: str, photo, idx: int) -> str:
    ext = Path(photo.filename).suffix
    taken = photo.taken_at or datetime.utcnow()
    return template.format(
        date=taken.strftime("%Y%m%d"),
        time=taken.strftime("%H%M%S"),
        seq=str(idx + 1).zfill(4),
        original=Path(photo.filename).stem,
        camera=photo.camera_model or "unknown",
    ) + ext


@router.get("/export/{job_id}/status", response_model=ExportJobResponse)
async def get_export_status(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(ExportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job
