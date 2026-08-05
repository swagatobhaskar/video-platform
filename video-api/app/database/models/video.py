from typing import List
import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import (
    String, DateTime, func, Text, Enum, ForeignKey, Boolean,
    Integer, Float, UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from typing import TYPE_CHECKING

from .upload import UploadSessionStatusEnum
from .processing import TranscodeTask, VideoEvent, VideoProcessingStatusEnum

# TYPE_CHECKING imports are ignored at runtime, so they don't create circular imports
if TYPE_CHECKING:
    from .upload import UploadSession, UploadSessionStatusEnum
    from .processing import TranscodeTask, VideoEvent

from app.config import get_settings
settings = get_settings()

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # One category -> many videos
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="category")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def r2_category_image_key(self) -> str | None:
        if self.image_url:
            return f"{settings.category_image_bucket_dev_url}/{self.image_url}"
        else:
            return None
        
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"

    
class Series(Base):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # One series -> many videos
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="series", passive_deletes=True)
    # With passive_delete=True, SQLAlchemy does not load or update the child rows
    # The DB handles it internally because of the foreign key.

    def __repr__(self) -> str:
        return f"<Series(id={self.id}, name='{self.name}')>"


class LanguageEnum(enum.Enum):
    HINDI = "hindi"
    BENGALI = "bengali"

class VideoPublicationStatusEnum(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Video(Base):
    __tablename__ = "videos"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(255), unique=False, index=True, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum), nullable=True, default=LanguageEnum.BENGALI)  
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)  # convert to ISO 8601 duration format when returning in API response
    
    publication_status: Mapped[VideoPublicationStatusEnum] = mapped_column(
        Enum(VideoPublicationStatusEnum),
        nullable=False,
        default=VideoPublicationStatusEnum.DRAFT
    )

    object_key: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True, index=True, nullable=True)

    # Many videos -> one category
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    category: Mapped["Category"] = relationship("Category", back_populates="videos")
    
    # Many videos -> one series
    series_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("series.id", ondelete="SET NULL"), nullable=True)
    series: Mapped["Series"] = relationship("Series", back_populates="videos")
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Using lazy="selectin" avoids calling .selectinload() in SQLAlchemy queries
    video_transcripts: Mapped[List["VideoTranscript"]] = relationship("VideoTranscript", back_populates="video", cascade="all, delete-orphan")
    video_events: Mapped[List["VideoEvent"]] = relationship("VideoEvent", back_populates="video", cascade="all, delete-orphan")
    # one-to-one relation with UploadSession and TranscodeTask
    upload_session: Mapped["UploadSession"] = relationship("UploadSession", back_populates="video", uselist=False, cascade="all, delete-orphan")
    transcode_task: Mapped["TranscodeTask"] = relationship("TranscodeTask", back_populates="video", uselist=False, cascade="all, delete-orphan")

    # SEO Fields
    seo_tags: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    focus_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secondary_keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    seo_summary_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thumbnail_alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    search_intent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # content_rating (G, PG, PG-13, R)
    # age_restriction (0, 7, 13, 18)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    thumbnail_object_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    bitrate: Mapped[int | None] = mapped_column(Integer, nullable=True)  # in kbps
    codec: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g., h264, vp9, av1
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)  # frames per second

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Admin manually clicks publish button to make the video live
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        # server_default=func.now(),
        nullable=True,  # Since the video is not published when it's created, we can't set server_default to now() and nullable to False.
    )

    # Keep properties that only use fields already loaded, along with the model.
    # Move properties that involve business rules.
    # Move properties that traverse relationships.

    @property
    def dash_manifest_key(self) -> str | None:
        if self.object_key:
            return f"{settings.processed_videos_bucket_dev_url}/{self.object_key}/dash/manifest.mpd"
        else:
            return None

    @property
    def hls_manifest_key(self) -> str | None:
        if self.object_key:
            return f"{settings.processed_videos_bucket_dev_url}/{self.object_key}/dash/master.m3u8"
        else:
            return None

    @property
    def thumbnail_key(self) -> str | None:
        if self.thumbnail_object_key:
            return f"{settings.thumbnails_bucket_dev_url}/{self.thumbnail_object_key}.webp" # extension might be removable
        else:
            return None

    @property
    def upload_status(self) -> str:
        if self.transcode_task:
            return self.transcode_task.status.value

        if self.upload_session:
            return self.upload_session.status.value

        return "unknown"


    @property
    def task_progress_percent(self) -> int | None:
        if self.transcode_task:
            return self.transcode_task.progress_percent
        return None


    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title='{self.title}', language='{self.language.value}')>"
    
    # VideoObject
    # {
    #     "@context": "https://schema.org",
    #     "@type": "VideoObject",
    #     "name": "The Haunted House Cartoon Story in Hindi",
    #     "description": "...",
    #     "thumbnailUrl": "...",
    #     "uploadDate": "2026-06-15",
    #     "duration": "PT12M30S",
    #     "contentUrl": "...",
    #     "embedUrl": "..."
    # }
    

class VideoTranscript(Base):
    __tablename__ = "video_transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="bn") # 'en', 'hi', 'bn'
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Many transcripts -> one video
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    video: Mapped["Video"] = relationship("Video", back_populates="video_transcripts")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # same language transcript shouldn't inserted twice for a video
    __table_args__ = (
        UniqueConstraint(
            "video_id",
            "language_code",
            name="uq_video_transcript_language"
        ),
    )

    def __repr__(self) -> str:
        return f"<VideoTranscript(id={self.id}, video_id={self.video_id}, language={self.language})"
