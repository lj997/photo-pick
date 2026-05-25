"""
光影甄选 - 后端应用入口

FastAPI 应用创建、中间件配置、路由注册。
启动时自动初始化数据库表结构。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.database import init_db
from app.api import sessions, photos, marks, groups, analysis, export, ws, filesystem


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Photo Pick", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(photos.router)
app.include_router(marks.router)
app.include_router(groups.router)
app.include_router(analysis.router)
app.include_router(export.router)
app.include_router(ws.router)
app.include_router(filesystem.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
