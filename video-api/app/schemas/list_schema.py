from pydantic import BaseModel, computed_field, ConfigDict
from datetime import datetime
import enum
import uuid
from app.config import get_settings

settings = get_settings()

class LanguageEnum(str, enum.Enum):
    HINDI = "hindi"
    BENGALI = "bengali"

class VideoPublicationStatusEnum(str, enum.Enum): # Recommended to inherit from str too
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

# "transcript": null,

class VideoListOut(BaseModel):
    # Pydantic v2 configuration to read from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_key: uuid.UUID

    category_id: str | None = None
    series_id: str | None = None

    title: str | None = None
    slug: str | None = None
    description: str | None = None
    created_at: datetime
    published_at: datetime | None = None
    updated_at: datetime
    episode_number: int | None = None
    thumbnail_alt_text: str | None = None
    thumbnail_object_storage_prefix: str | None = None
    language: LanguageEnum | None = None
    bitrate: int | None = None
    codec: str | None = None
    view_count: int = 0
    like_count: int = 0
    dislike_count: int = 0
    width: int | None = None
    height: int | None = None 
    fps: float | None = None
    duration_seconds: float | None = None
    publication_status: VideoPublicationStatusEnum

    # --- COMPUTED URL FIELDS (Leveraging the model's properties) ---

    @computed_field
    @property
    def thumbnail_url(self) -> str | None:
        if not self.thumbnail_object_storage_prefix:
            return None
        return f"{settings.thumbnails_bucket_dev_url}/{self.thumbnail_object_storage_prefix}"

    @computed_field
    @property
    def hls_url(self) -> str | None:
        if not self.id:
            return None
        return f"{settings.processed_videos_bucket_dev_url}/{self.object_key}/dash/master.m3u8"

    @computed_field
    @property
    def dash_url(self) -> str | None:
        if not self.id:
            return None
        return f"{settings.processed_videos_bucket_dev_url}/{self.object_key}/dash/manifest.mpd"

class VideoSEOOut(BaseModel):
    meta_title: str | None = None
    seo_summary_en: str | None = None
    meta_description: str | None = None
    keywords: list[str | None]
    seo_tags: list[str | None]
    search_intent: str | None = None
    focus_keyword: str | None = None
    secondary_keywords: list[str | None]
    