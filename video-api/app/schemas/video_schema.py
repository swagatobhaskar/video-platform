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


class VideoCreate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None

    language: LanguageEnum | None = None

    category_id: uuid.UUID | None = None
    series_id: uuid.UUID | None = None
    episode_number: int | None = None

    seo_tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    secondary_keywords: list[str] = Field(default_factory=list)

    focus_keyword: str | None = None
    seo_summary_en: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    thumbnail_alt_text: str | None = None
    search_intent: str | None = None


class VideoUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    language: LanguageEnum | None = None

    category_id: uuid.UUID | None = None
    series_id: uuid.UUID | None = None
    episode_number: int | None = None

    seo_tags: list[str] | None = None
    keywords: list[str] | None = None
    secondary_keywords: list[str] | None = None

    focus_keyword: str | None = None
    seo_summary_en: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    thumbnail_alt_text: str | None = None
    search_intent: str | None = None


class VideoSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    slug: str | None

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

    language: LanguageEnum | None
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

    transcript: str | None

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
    upload_sessions: list[UploadSessionRead] = Field(default_factory=list)
    transcode_tasks: list[TranscodeTaskRead] = Field(default_factory=list)
    video_events: list[VideoEventRead] = Field(default_factory=list)

    dash_manifest_key: str | None
    hls_manifest_key: str | None
    thumbnail_object_key: str | None

    thumbnail_uploaded: bool
    transcript_uploaded: bool
    metadata_complete: bool
    seo_fields_complete: bool
    video_uploaded: bool
    can_publish: bool


# Might not be required anymore
# class VideoOut(BaseModel):
#     # Pydantic v2 configuration to read from SQLAlchemy models
#     model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

#     id: uuid.UUID
#     object_key: uuid.UUID | None = None # it can be None until video is processed
#     category_id: uuid.UUID | None = None
#     series_id: uuid.UUID | None = None
#     title: str | None = None
#     slug: str | None = None
#     description: str | None = None
#     created_at: datetime
#     published_at: datetime | None = None
#     updated_at: datetime
#     episode_number: int | None = None
#     thumbnail_alt_text: str | None = None
#     thumbnail_object_storage_prefix: str | None = None
#     language: LanguageEnum | None = None
#     bitrate: int | None = None
#     codec: str | None = None
#     view_count: int = 0
#     like_count: int = 0
#     dislike_count: int = 0
#     width: int | None = None
#     height: int | None = None 
#     fps: float | None = None
#     duration_seconds: float | None = None
#     publication_status: VideoPublicationStatusEnum
