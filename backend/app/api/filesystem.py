"""
文件系统浏览 API

为前端文件夹选择器提供目录浏览功能。
Windows 系统返回磁盘驱动器列表，其他系统从根目录开始。
"""
import platform
import string
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/filesystem", tags=["filesystem"])


@router.get("/browse")
async def browse_folders(path: str = Query(default="")):
    if not path:
        return _list_drives()

    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"路径不存在: {path}")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail=f"不是文件夹: {path}")

    folders = sorted(
        [item.name for item in p.iterdir() if item.is_dir() and not item.name.startswith(".")],
        key=str.lower,
    )

    parent = str(p.parent) if p.parent != p else None

    return {
        "current": str(p),
        "parent": parent,
        "folders": folders,
    }


def _list_drives():
    if platform.system() == "Windows":
        drives = []
        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:\\")
            if drive.exists():
                drives.append(f"{letter}:\\")
        return {
            "current": "",
            "parent": None,
            "folders": drives,
        }
    else:
        return {
            "current": "/",
            "parent": None,
            "folders": sorted(
                [item.name for item in Path("/").iterdir() if item.is_dir() and not item.name.startswith(".")],
                key=str.lower,
            ),
        }
