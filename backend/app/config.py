"""
应用配置模块

通过环境变量或 .env 文件加载配置，前缀 PHOTO_PICK_。
启动时自动创建数据目录。
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Photo Pick"
    debug: bool = False

    data_dir: Path = Path("../data")
    cache_dir: Path = Path("../data/cache")
    db_dir: Path = Path("../data/db")

    thumbnail_sm_size: int = 300
    thumbnail_lg_size: int = 1920
    thumbnail_quality_sm: int = 85
    thumbnail_quality_lg: int = 90
    thumbnail_workers: int = 4

    grouping_time_threshold_seconds: float = 2.0
    similarity_hash_threshold: int = 8

    cloud_api_key: str = ""
    cloud_enabled: bool = False

    class Config:
        env_file = ".env"
        env_prefix = "PHOTO_PICK_"


settings = Settings()

settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.cache_dir.mkdir(parents=True, exist_ok=True)
settings.db_dir.mkdir(parents=True, exist_ok=True)
