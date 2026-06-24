from typing import List
import uuid
from datetime import datetime
import enum

from sqlalchemy import (
    String, DateTime, func, Text, Enum, ForeignKey, Boolean,
    Integer, Float, UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from typing import TYPE_CHECKING

# TYPE_CHECKING imports are ignored at runtime, so they don't create circular imports
if TYPE_CHECKING:
    from .upload import UploadSession, UploadSessionStatusEnum
    from .processing import TranscodeTask, VideoEvent

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)

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
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="series")

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
    title: Mapped[str] = mapped_column(String(255), unique=False, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum), nullable=False, default=LanguageEnum.BENGALI)  
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)  # convert to ISO 8601 duration format when returning in API response
    
    publication_status: Mapped[VideoPublicationStatusEnum] = mapped_column(
        Enum(VideoPublicationStatusEnum),
        nullable=False,
        default=VideoPublicationStatusEnum.DRAFT
    )

    # Many videos -> one category
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=False)
    category: Mapped["Category"] = relationship("Category", back_populates="videos")
    
    # Many videos -> one series
    series_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("series.id", ondelete="SET NULL"), nullable=True)
    series: Mapped["Series"] = relationship("Series", back_populates="videos")
    episode_number: Mapped[int] = mapped_column(Integer, nullable=True)

    # Children
    video_transcripts: Mapped[List["VideoTranscript"]] = relationship("VideoTranscript", back_populates="video", cascade="all, delete-orphan")
    upload_sessions: Mapped[List["UploadSession"]] = relationship("UploadSession", back_populates="video", cascade="all, delete-orphan")
    transcode_tasks: Mapped[List["TranscodeTask"]] = relationship("TranscodeTask", back_populates="video", cascade="all, delete-orphan")
    # renditions: Mapped[List[Rendition]] = relationship("Rendition", back_populates="video", cascade="all, delete-orphan")
    video_events: Mapped[List["VideoEvent"]] = relationship("VideoEvent", back_populates="video", cascade="all, delete-orphan")

    # SEO Fields
    seo_tags: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    focus_keyword: Mapped[str] = mapped_column(String(255), nullable=True)
    secondary_keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    seo_summary_en: Mapped[str] = mapped_column(String(255), nullable=True)
    keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    meta_title: Mapped[str] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str] = mapped_column(String(255), nullable=True)
    thumbnail_alt_text: Mapped[str] = mapped_column(String(255), nullable=True)
    search_intent: Mapped[str] = mapped_column(String(255), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)

    # content_rating (G, PG, PG-13, R)
    # age_restriction (0, 7, 13, 18)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # e.g., if object_prefix = "bucket/abc123"
    # Then construct:
    # dash_manifest = f"{prefix}/dash/manifest.mpd"
    # hls_manifest = f"{prefix}/hls/master.m3u8"
    # Not required for my use case
    # video_object_storage_prefix: Mapped[str] = mapped_column(String(255), nullable=True)

    # Thumbnail should be prefixed by the video_id
    thumbnail_object_storage_prefix: Mapped[str] = mapped_column(String(255), nullable=True)
    
    bitrate: Mapped[int] = mapped_column(Integer, nullable=True)  # in kbps
    codec: Mapped[str] = mapped_column(String, nullable=True)  # e.g., h264, vp9, av1
    width: Mapped[int] = mapped_column(Integer, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    fps: Mapped[float] = mapped_column(Float, nullable=True)  # frames per second

    # These aren't required, since file will be stored in the *_OBJECT_STORAGE_PREFIX above:
    # video_dash_url: Mapped[str] = mapped_column(String(255), nullable=True)
    # video_hls_url: Mapped[str] = mapped_column(String(255), nullable=True)
    # thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=True)

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
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # server_default=func.now(),
        nullable=True,  # Since the video is not published when it's created, we can't set server_default to now() and nullable to False.
    )

    @property
    def dash_manifest(self):
        return f"{self.video_object_storage_prefix}/dash/manifest.mpd"

    @property
    def hls_manifest(self):
        return f"{self.video_object_storage_prefix}/hls/master.m3u8"    # correction required here

    @property
    def thumbnail_uploaded(self) -> bool:
        return bool(self.thumbnail_object_storage_prefix)
    
    @property
    def transcript_uploaded(self) -> bool:
        return any(
            transcript.transcript_text
            for transcript in self.video_transcripts
        )
    
    @property
    def metadata_complete(self) -> bool:
        return all([
            self.title,
            self.description,
            self.category_id,
            self.slug,
            self.language,
        ])
    
    @property
    def seo_fields_complete(self) -> bool:
        return all([
            self.search_intent,
            self.focus_keyword,
            self.keywords,
            self.seo_tags,
            self.seo_summary_en,
            self.secondary_keywords,
            self.thumbnail_alt_text,
            self.meta_description,
            self.meta_title,
        ])

    @property
    def video_uploaded(self) -> bool:
        return any(
            session.status == UploadSessionStatusEnum.COMPLETED
            for session in self.upload_sessions
        )

    @property
    def can_publish(self) -> bool:
        return (
            self.video_uploaded and self.thumbnail_uploaded and self.metadata_complete
        )

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
    transcript_text: Mapped[str] = mapped_column(Text, nullable=True)

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
