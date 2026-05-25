"""
ORM 数据模型

定义所有数据库表结构：
- Session: 选片会话（对应一个导入的文件夹）
- Photo: 照片记录（含 EXIF 信息、评分标记、缩略图状态）
- Group / GroupMember: 连拍分组
- AnalysisResult: 质量分析结果
- ExportJob: 导出任务记录
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    folder_path: Mapped[str] = mapped_column(String, nullable=False)
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photos: Mapped[list["Photo"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    groups: Mapped[list["Group"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    format: Mapped[str | None] = mapped_column(String)

    taken_at: Mapped[datetime | None] = mapped_column(DateTime)
    camera_make: Mapped[str | None] = mapped_column(String)
    camera_model: Mapped[str | None] = mapped_column(String)
    lens: Mapped[str | None] = mapped_column(String)
    focal_length: Mapped[float | None] = mapped_column(Float)
    aperture: Mapped[float | None] = mapped_column(Float)
    shutter_speed: Mapped[str | None] = mapped_column(String)
    iso: Mapped[int | None] = mapped_column(Integer)

    stars: Mapped[int] = mapped_column(Integer, default=0)
    color_label: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")

    thumb_sm_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    thumb_lg_ready: Mapped[bool] = mapped_column(Boolean, default=False)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="photos")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(back_populates="photo", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_photos_session", "session_id"),
        Index("idx_photos_stars", "session_id", "stars"),
        Index("idx_photos_status", "session_id", "status"),
        Index("idx_photos_color", "session_id", "color_label"),
        Index("idx_photos_taken", "session_id", "taken_at"),
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    name: Mapped[str | None] = mapped_column(String)
    group_type: Mapped[str] = mapped_column(String, default="burst")
    pick_photo_id: Mapped[str | None] = mapped_column(String, ForeignKey("photos.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="groups")
    members: Mapped[list["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[str] = mapped_column(String, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    photo_id: Mapped[str] = mapped_column(String, ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    group: Mapped["Group"] = relationship(back_populates="members")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    photo_id: Mapped[str] = mapped_column(String, ForeignKey("photos.id", ondelete="CASCADE"))
    analysis_type: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    result_data: Mapped[str | None] = mapped_column(Text)
    is_issue: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    photo: Mapped["Photo"] = relationship(back_populates="analysis_results")

    __table_args__ = (
        Index("idx_analysis_photo", "photo_id"),
        Index("idx_analysis_type", "photo_id", "analysis_type"),
    )


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    config: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
