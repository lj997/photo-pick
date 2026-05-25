"""
数据库连接管理

使用 SQLAlchemy 异步引擎 + aiosqlite 驱动连接 SQLite 数据库。
提供 get_db 依赖注入和 init_db 表初始化。
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.db_dir / 'photo_pick.db'}"

engine = create_async_engine(DATABASE_URL, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
