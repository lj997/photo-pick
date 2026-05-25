from datetime import datetime
from pydantic import BaseModel


class SessionCreate(BaseModel):
    path: str


class SessionResponse(BaseModel):
    id: str
    name: str
    folder_path: str
    photo_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoResponse(BaseModel):
    id: str
    session_id: str
    filename: str
    filepath: str
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    taken_at: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens: str | None = None
    focal_length: float | None = None
    aperture: float | None = None
    shutter_speed: str | None = None
    iso: int | None = None
    stars: int = 0
    color_label: str | None = None
    status: str = "pending"
    thumb_sm_ready: bool = False
    thumb_lg_ready: bool = False
    sort_order: int = 0

    class Config:
        from_attributes = True


class PhotoListResponse(BaseModel):
    total: int
    photos: list[PhotoResponse]


class MarkUpdate(BaseModel):
    stars: int | None = None
    color_label: str | None = None
    status: str | None = None


class BatchMarkUpdate(BaseModel):
    photo_ids: list[str]
    marks: MarkUpdate


class GroupResponse(BaseModel):
    id: str
    session_id: str
    name: str | None = None
    group_type: str
    pick_photo_id: str | None = None
    member_count: int = 0
    members: list[PhotoResponse] = []

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    id: str
    photo_id: str
    analysis_type: str
    score: float | None = None
    result_data: str | None = None
    is_issue: bool = False

    class Config:
        from_attributes = True


class ExportConfig(BaseModel):
    destination: str
    mode: str = "copy"  # copy or move
    group_by: str | None = None  # None=flat, "status", "color", "stars"
    filter_stars_min: int | None = None
    filter_status: list[str] | None = None
    filter_colors: list[str] | None = None
    rename_template: str | None = None


class ExportJobResponse(BaseModel):
    id: str
    status: str
    total_count: int
    processed_count: int

    class Config:
        from_attributes = True
