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


# --- 照片整理相关 ---

class OrganizeFilter(BaseModel):
    stars_min: int | None = None
    status: list[str] | None = None
    colors: list[str] | None = None
    tag: str | None = None


class OrganizeConfig(BaseModel):
    destination: str
    mode: str = "copy"  # copy or move
    group_by: list[str] = ["month"]  # date, month, year, status, stars, color, camera, lens, format, tag:scene
    filters: OrganizeFilter | None = None
    rename_template: str | None = None
    include_note_template: bool = True
    manual_paths: dict[str, str] | None = None  # photo_id -> relative folder path


class OrganizePhotoPreview(BaseModel):
    id: str
    filename: str
    target_path: str
    taken_at: datetime | None = None
    camera_model: str | None = None
    lens: str | None = None
    format: str | None = None
    file_size: int | None = None
    stars: int = 0
    color_label: str | None = None
    status: str = "pending"
    tags: list[str] = []


class OrganizeGroupPreview(BaseModel):
    path: str
    count: int
    sample_filenames: list[str] = []
    photos: list[OrganizePhotoPreview] = []


class OrganizePreviewResponse(BaseModel):
    total: int
    destination: str
    groups: list[OrganizeGroupPreview]


class OrganizeResultResponse(BaseModel):
    total: int
    processed: int
    skipped: int
    destination: str
    note_path: str | None = None


class NoteReadResponse(BaseModel):
    path: str
    exists: bool
    content: str = ""


class NoteSaveRequest(BaseModel):
    directory: str
    filename: str = "PHOTO_STORY.md"
    content: str


class NoteSaveResponse(BaseModel):
    path: str
    saved: bool = True


# --- AI 标签相关 ---

class AISettingsResponse(BaseModel):
    ai_enabled: bool = False
    ai_provider: str = "claude"
    ai_model_name: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""


class AISettingsUpdate(BaseModel):
    ai_enabled: bool | None = None
    ai_provider: str | None = None
    ai_model_name: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None


class PhotoTagResponse(BaseModel):
    id: str
    photo_id: str
    dimension: str
    tag_value: str
    source: str = "ai"
    confidence: float | None = None

    class Config:
        from_attributes = True


class PhotoTagCreate(BaseModel):
    dimension: str
    tag_value: str


class TagCount(BaseModel):
    value: str
    count: int


class TagDimensionSummary(BaseModel):
    dimension: str
    tags: list[TagCount]


class TagSummaryResponse(BaseModel):
    dimensions: list[TagDimensionSummary]


class LocalTagAnalysisResponse(BaseModel):
    total: int
    tagged: int
    tags_created: int
    mode: str = "vision"
    failed: int = 0


class LocalTagAnalysisRequest(BaseModel):
    mode: str = "vision"  # rules or vision
