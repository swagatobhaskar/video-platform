from pydantic import BaseModel, computed_field, ConfigDict, Field
from datetime import datetime
import uuid
from app.config import get_settings
from app.database.models import (
    VideoPublicationStatusEnum, LanguageEnum, UploadSessionStatusEnum,
    VideoProcessingStatusEnum
)

settings = get_settings()


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    image_url: str | None = None


class SeriesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class VideoTranscriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    language_code: str
    transcript_text: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadPartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    part_number: int
    etag: str
    size_bytes: int
    uploaded_at: datetime


class UploadSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_key: str | None = None
    video_upload_id: str | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    original_filename: str | None = None
    total_parts: int | None = None
    uploaded_parts_count: int = 0
    status: UploadSessionStatusEnum

    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    parts: list[UploadPartRead] = Field(default_factory=list)


class VideoEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    payload: dict | None = None
    created_at: datetime


class TranscodeTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: VideoProcessingStatusEnum
    progress_percent: int = 0
    worker_id: str | None = None
    error_message: str | None = None
    retry_count: int = 0

    started_at: datetime | None = None
    finished_at: datetime | None = None
    heartbeat_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


# class VideoCreate(BaseModel):
#     title: str | None = None
#     slug: str | None = None
#     description: str | None = None

#     language: LanguageEnum | None = None

#     category_id: uuid.UUID | None = None
#     series_id: uuid.UUID | None = None
#     episode_number: int | None = None

#     seo_tags: list[str] = Field(default_factory=list)
#     keywords: list[str] = Field(default_factory=list)
#     secondary_keywords: list[str] = Field(default_factory=list)

#     focus_keyword: str | None = None
#     seo_summary_en: str | None = None
#     meta_title: str | None = None
#     meta_description: str | None = None
#     thumbnail_alt_text: str | None = None
#     search_intent: str | None = None


# class VideoUpdate(BaseModel):
#     title: str | None = None
#     slug: str | None = None
#     description: str | None = None
#     language: LanguageEnum | None = None

#     category_id: uuid.UUID | None = None
#     series_id: uuid.UUID | None = None
#     episode_number: int | None = None

#     seo_tags: list[str] | None = None
#     keywords: list[str] | None = None
#     secondary_keywords: list[str] | None = None

#     focus_keyword: str | None = None
#     seo_summary_en: str | None = None
#     meta_title: str | None = None
#     meta_description: str | None = None
#     thumbnail_alt_text: str | None = None
#     search_intent: str | None = None


class VideoMetadataUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    language: LanguageEnum | None = None
    category_id: uuid.UUID | None = None
    series_id: uuid.UUID | None = None
    episode_number: int | None = None


class VideoMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    language: LanguageEnum | None = None
    category_id: uuid.UUID | None = None
    series_id: uuid.UUID | None = None
    episode_number: int | None = None


class VideoSEOUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    seo_tags: list[str] | None = None
    keywords: list[str] | None = None
    secondary_keywords: list[str] | None = None

    focus_keyword: str | None = None
    seo_summary_en: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    thumbnail_alt_text: str | None = None
    search_intent: str | None = None


class VideoSEORead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    seo_tags: list[str] | None = None
    keywords: list[str] | None = None
    secondary_keywords: list[str] | None = None

    focus_keyword: str | None = None
    seo_summary_en: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    thumbnail_alt_text: str | None = None
    search_intent: str | None = None


"""
Example SEO data format:
{
  "seo_tags": [
    "technology",
    "artificial intelligence",
    "AI news",
    "machine learning"
  ],
  "keywords": [
    "AI technology trends",
    "latest AI developments",
    "future of artificial intelligence"
  ],
  "secondary_keywords": [
    "deep learning",
    "automation",
    "AI tools",
    "digital transformation"
  ],
  "focus_keyword": "artificial intelligence trends",
  "seo_summary_en": "Explore the latest artificial intelligence trends, innovations, and how AI is transforming industries worldwide.",
  "meta_title": "Artificial Intelligence Trends and Latest Innovations",
  "meta_description": "Discover the latest AI trends, emerging technologies, and how artificial intelligence is shaping the future of businesses and everyday life.",
  "thumbnail_alt_text": "Artificial intelligence technology concept with digital graphics",
  "search_intent": "informational"
}
"""


class VideoSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    slug: str | None
    object_key: str | None = None
    thumbnail_object_key: str | None

    publication_status: VideoPublicationStatusEnum

    duration_seconds: float | None

    view_count: int
    like_count: int

    created_at: datetime
    published_at: datetime | None


class VideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    title: str | None
    slug: str | None
    description: str | None

    language: LanguageEnum = LanguageEnum.BENGALI
    duration_seconds: float | None

    publication_status: VideoPublicationStatusEnum

    object_key: uuid.UUID | None

    category_id: uuid.UUID | None
    series_id: uuid.UUID | None
    episode_number: int | None

    seo_tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    secondary_keywords: list[str] = Field(default_factory=list)

    focus_keyword: str | None
    seo_summary_en: str | None
    meta_title: str | None
    meta_description: str | None
    thumbnail_alt_text: str | None
    search_intent: str | None

    thumbnail_object_key: str | None

    bitrate: int | None
    codec: str | None
    width: int | None
    height: int | None
    fps: float | None

    view_count: int
    like_count: int
    dislike_count: int

    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    category: CategoryRead | None = None
    series: SeriesRead | None = None

    video_transcripts: list[VideoTranscriptRead] = Field(default_factory=list)

    dash_manifest_key: str | None
    hls_manifest_key: str | None
    thumbnail_object_key: str | None

    # These now come from VideoService
    # 
    # thumbnail_uploaded: bool
    # transcript_uploaded: bool
    # missing_metadata_fields: list[str]
    # missing_seo_fields: list[str]
    # video_uploaded: bool
    # can_publish: bool


class VideoUploadHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    slug: str | None
    language: LanguageEnum = LanguageEnum.BENGALI
    # category_id: uuid.UUID | None
    # series_id: uuid.UUID | None
    episode_number: int | None
    thumbnail_object_key: str | None
    created_at: datetime
    category: CategoryRead | None = None
    series: SeriesRead | None = None
    video_status: str
    progress_percent: int | None


class VideoAdminRead(BaseModel):
    # these fields aren't in VideoRead
    upload_session: UploadSessionRead = Field(default_factory=list)
    transcode_task: TranscodeTaskRead = Field(default_factory=list)
    video_events: list[VideoEventRead] = Field(default_factory=list)


class VideoActionRequiredResponse(BaseModel):
    video_id: uuid.UUID
    title: str | None
    upload_status: str | None
    transcoded: bool = False
    errors: dict[str, list[str]]
    