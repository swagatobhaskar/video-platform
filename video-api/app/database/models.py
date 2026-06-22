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

from app.database.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
    

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
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="series")

    def __repr__(self) -> str:
        return f"<Series(id={self.id}, name='{self.name}')>"


class LanguageEnum(enum.Enum):
    HINDI = "hindi"
    BENGALI = "bengali"

class VideoStatusEnum(enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"

class Video(Base):
    __tablename__ = "videos"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), unique=False, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum), nullable=False, default=LanguageEnum.BENGALI)  
    
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)  # convert to ISO 8601 duration format when returning in API response
    status: Mapped[VideoStatusEnum] = mapped_column(Enum(VideoStatusEnum), nullable=False, default=VideoStatusEnum.DRAFT)

    # Many videos -> one category
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=False)
    category: Mapped["Category"] = relationship("Category", back_populates="videos")
    
    # Many videos -> one series
    series_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("series.id", ondelete="SET NULL"), nullable=True)
    series: Mapped["Series"] = relationship("Series", back_populates="videos")

    # Children
    upload_sessions: Mapped[List[UploadSession]] = relationship("UploadSession", back_populates="video", cascade="all, delete-orphan")
    transcode_tasks: Mapped[List[TranscodeTask]] = relationship("TranscodeTask", back_populates="video", cascade="all, delete-orphan")
    # renditions: Mapped[List[Rendition]] = relationship("Rendition", back_populates="video", cascade="all, delete-orphan")
    video_events: Mapped[List[VideoEvent]] = relationship("VideoEvent", back_populates="video", cascade="all, delete-orphan")

    # SEO Fields
    seo_tags: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    focus_keyword: Mapped[str] = mapped_column(String(255), nullable=True)
    secondary_keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=True)
    seo_summary_en: Mapped[str] = mapped_column(String(255), nullable=True)
    keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    meta_title: Mapped[str] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str] = mapped_column(String(255), nullable=True)
    thumbnail_alt_text: Mapped[str] = mapped_column(String(255), nullable=True)
    search_intent: Mapped[str] = mapped_column(String(255), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    # transcript_hindi
    # transcript_bengali
    # transcript_english
    # transcript_native
    # content_rating (G, PG, PG-13, R)
    # age_restriction (0, 7, 13, 18)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # e.g.,
    # If object_prefix = "bucket/abc123"
    # Then construct:
    # dash_manifest = f"{prefix}/dash/manifest.mpd"
    # hls_manifest = f"{prefix}/hls/master.m3u8"
    video_object_storage_prefix: Mapped[str] = mapped_column(String(255), nullable=True)
    thumbnail_object_storage_prefix: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # These aren't required, since file will be stored in the *_OBJECT_STORAGE_PREFIX above:
    # r2_video_dash_url: Mapped[str] = mapped_column(String(255), nullable=True)
    # r2_video_hls_url: Mapped[str] = mapped_column(String(255), nullable=True)
    # r2_thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=True)

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
        return f"{self.video_object_storage_prefix}/hls/master.m3u8"
    
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
    

class UploadSessionStatusEnum(enum.Enum):
    IDLE = "idle"
    CREATED = "created"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    video: Mapped["Video"] = relationship("Video", back_populates="upload_sessions")

    # object_key = “path in object storage” / what file in R2 this upload session is writing to
    object_key: Mapped[str] = mapped_column(String(255), nullable=True)
    
    r2_video_upload_id: Mapped[str] = mapped_column(String(255), nullable=False)
    r2_thumbnail_upload_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    file_size_bytes: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # optional, can be calculated after upload is complete using ETags of all parts/chunks and stored in videos table
    checksum: Mapped[str] = mapped_column(String(255), nullable=True)

    # total number of parts/chunks the video is divided into for multipart upload
    total_parts: Mapped[int] = mapped_column(Integer, nullable=False)
    # number of parts/chunks successfully uploaded so far
    uploaded_parts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # uploaded_parts: Mapped[list["UploadPart"]] = relationship()
        
    metadata_complete: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    # video_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False) ? 
    # thumbnail_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False) ?
    
    status: Mapped[UploadSessionStatusEnum] = mapped_column(
        Enum(UploadSessionStatusEnum),
        nullable=False,
        default=UploadSessionStatusEnum.IDLE
    )
    
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
        return f"<UploadSession(id={self.id}, video_id={self.video_id})>"
    

class UploadPart(Base):
    __tablename__ = "upload_parts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    # Many upload parts -> one upload session
    upload_session: Mapped["UploadSession"] = relationship("UploadSession")
    part_number: Mapped[int] = mapped_column(nullable=False)
    etag: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("upload_session_id", "part_number", name="uq_upload_session_part_number"),
    )
    
    def __repr__(self) -> str:
        return f"<UploadPart(id={self.id}, video_id={self.video_id}, upload_session_id={self.upload_session_id})>"
    

class VideoProcessingStatusEnum(enum.Enum):
    IDLE = "idle"
    PENDING = "pending"
    DOWNLOADING_VIDEO = "Downloading_video"
    PROBING = "probing"
    TRANSCODING = "transcoding"
    UPLOADING = "uploading"
    CLEANUP = "cleanup"
    COMPLETED = "completed"
    FAILED = "failed"
    
class TranscodeTask(Base):
    __tablename__ = "transcode_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    video: Mapped["Video"] = relationship("Video", back_populates="transcode_tasks")
        
    upload_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    upload_session: Mapped["UploadSession"] = relationship("UploadSession")

    status: Mapped[VideoProcessingStatusEnum] = mapped_column(
        Enum(VideoProcessingStatusEnum),
        nullable=False,
        default=VideoProcessingStatusEnum.IDLE
    )
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    worker_id: Mapped[str] = mapped_column(String(255), nullable=True)
    job_external_id: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # server_default=func.now(),
        nullable=True,
    )
        
    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # server_default=func.now(),
        nullable=True,
    )
        
    heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # server_default=func.now(),
        nullable=True,
    )

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

"""
Video Events:
    NOT_STARTED
    UPLOAD_STARTED
    CHUNKS_UPLOADED
    CHUNKS_UPLOAD_PAUSED
    CHUNKS_UPLOAD_RESUMED
    CHUNKS_UPLOAD_RETRY
    CHUNKS_UPLOAD_FAILED
    CHUNKS_UPLOAD_ABORTED
    DOWNLOAD_STARTED
    FFPROBE_COMPLETED
    TRANSCODE_720P_DONE
    UPLOAD_FINISHED
    ...
"""

class VideoEvent(Base):
    __tablename__ = "processing_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transcode_task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transcode_tasks.id"))
    transcode_task: Mapped["TranscodeTask"] = relationship("TranscodeTask")

    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    video: Mapped["Video"] = relationship("Video", back_populates="video_events")

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, default="NOT_STARTED")
    message: Mapped[str] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=True)

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
        return f"<VideoEvent(id={self.id}, transcode_task_id={self.transcode_task_id}, \
             video_id={self.video_id}, event_type={self.event_type})>"
    

# class RenditionTypeEnum(enum.Enum):
#     HLS = "hls"
#     DASH = "dash"
    # MP4 = "mp4"

# class Rendition(Base):
#     __tablename__ = "renditions"

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
#     video: Mapped["Video"] = relationship("Video", back_populates="renditions")
    
#     type: Mapped[RenditionTypeEnum] = mapped_column(Enum(RenditionTypeEnum), nullable=False, default=RenditionTypeEnum.HLS)  # hls / dash
#     resolution: Mapped[str] = mapped_column(String)  # 360p / 720p / 1080p
#     object_key: Mapped[str] = mapped_column(String)  # R2 path
#     # url is the public URL to access the rendition, which can be constructed using
#     # the object_key and R2 bucket URL, but we can also store it here for easy access
#     url: Mapped[str] = mapped_column(String)

#     bitrate: Mapped[int] = mapped_column(Integer, nullable=True)  # in kbps
#     codec: Mapped[str] = mapped_column(String, nullable=True)  # e.g., h264, vp9, av1
#     width: Mapped[int] = mapped_column(Integer, nullable=True)
#     height: Mapped[int] = mapped_column(Integer, nullable=True)
#     fps: Mapped[float] = mapped_column(Float, nullable=True)  # frames per second

#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         nullable=False,
#     )

#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         onupdate=func.now(),
#         nullable=False,
#     )

#     def __repr__(self) -> str:
#         return f"<Rendition(id={self.id}, video_id={self.video_id}, type={self.type.value}, resolution={self.resolution})>"
