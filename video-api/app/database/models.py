from typing import List
import uuid
from datetime import datetime
import enum

from sqlalchemy import String, DateTime, func, Text, Enum, ForeignKey, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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
        return f"<User(id={self.id}, email='{self.email}')>"
    
    
class Category(Base):
    __tablename__ = "categories"

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
    
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # One category -> many videos
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="category", cascade="all, delete-orphan")
    
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
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum), nullable=False, default=LanguageEnum.BENGALI)  
    
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    # Many videos -> one category
    category: Mapped["Category"] = relationship("Category", back_populates="videos")
    
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)  # convert to ISO 8601 duration format when returning in API response
    status: Mapped[VideoStatusEnum] = mapped_column(Enum(VideoStatusEnum), nullable=False, default=VideoStatusEnum.DRAFT)

    seo_tags: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    # focus_keyword
    # secondary_keywords
    # series_name
    # episode_number
    # transcript
    # transcript_hindi
    # transcript_bengali
    # transcript_english
    # transcript_native
    # seo_summary_en
    # keywords
    # meta_title
    # meta_description
    # thumbnail_alt_text
    # view_count
    # like_count
    # search_intent
    # content_rating (G, PG, PG-13, R)
    # age_restriction (0, 7, 13, 18)
    
    
    # r2_video_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
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
        nullable=False,
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
    
class VideoUploadStatusEnum(enum.Enum):
    IDLE = "idle"
    PENDING = "pending"
    UPLOADING = "uploading"
    PAUSED = "paused"
    SUCCESSFUL = "successful"
    RETRY = "retry"
    FAILED = "failed"

class MetadataFormStatusEnum(enum.Enum):
    EMPTY = "empty"
    PARTIAL = "partial"
    COMPLETE = "complete"

class UploadSessionStatusEnum(enum.Enum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    video: Mapped["Video"] = relationship("Video")

    # object_key = “path in object storage” / what file in R2 this upload session is writing to
    object_key: Mapped[str] = mapped_column(String(255), nullable=True)
    
    r2_video_upload_id: Mapped[str] = mapped_column(String(255), nullable=False)
    r2_thumbnail_upload_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # total number of parts/chunks the video is divided into for multipart upload
    total_parts: Mapped[int] = mapped_column(Integer, nullable=False)
    # number of parts/chunks successfully uploaded so far
    uploaded_parts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # uploaded_parts: Mapped[list["UploadPart"]] = relationship()
    
    video_upload_status: Mapped[VideoUploadStatusEnum] = mapped_column(
        Enum(VideoUploadStatusEnum),
        nullable=False,
        default=VideoUploadStatusEnum.IDLE
    )
    
    metadataform_status: Mapped[MetadataFormStatusEnum] = mapped_column(
        Enum(MetadataFormStatusEnum),
        nullable=False,
        default=MetadataFormStatusEnum.EMPTY
    )
    
    thumbnail_uploaded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    upload_session_status: Mapped[UploadSessionStatusEnum] = mapped_column(
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
    
    part_number: Mapped[int] = mapped_column(nullable=False)
    
    etag: Mapped[str] = mapped_column(String(255), nullable=False)
    
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<UploadPart(id={self.id}, video_id={self.video_id}, upload_session_id={self.upload_session_id})>"
    

class TranscodingProgressEnum(enum.Enum):
# Status          Progress
# queued          0
# downloading     10
# processing      30
# transcoding     70
# uploading       90
# cleanup         95
# completed       100
        QUEUED = "queued"
        DOWNLOADING = "downloading"
        PROCESSING = "processing"
        TRANSCODING = "transcoding"
        UPLOADING = "uploading"
        CLEANUP = "cleanup"
        COMPLETED = "completed"

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
    video: Mapped["Video"] = relationship("Video")
        
    upload_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    upload_session: Mapped["UploadSession"] = relationship("UploadSession")

    status: Mapped[VideoProcessingStatusEnum] = mapped_column(Enum(VideoProcessingStatusEnum), nullable=False, default=VideoProcessingStatusEnum.IDLE)
        
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
        
    worker_id: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
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
        
    # created_at:
    # updated_at:
        
    heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # server_default=func.now(),
        nullable=True,
    )
    
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class VideoEventEnum(enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    UPLOAD_STARTED = "UPLOAD_STARTED"
    CHUNKS_UPLOADED = "CHUNKS_UPLOADED"
    CHUNKS_UPLOAD_PAUSED = "CHUNKS_UPLOAD_PAUSED"
    CHUNKS_UPLOAD_RESUMED = "CHUNKS_UPLOAD_RESUMED"
    CHUNKS_UPLOAD_RETRY = "CHUNKS_UPLOAD_RETRY"
    CHUNKS_UPLOAD_FAILED = "CHUNKS_UPLOAD_FAILED"
    CHUNKS_UPLOAD_ABORTED = "CHUNKS_UPLOAD_ABORTED"
    DOWNLOAD_STARTED = "DOWNLOAD_STARTED"
    FFPROBE_COMPLETED = "FFPROBE_COMPLETED"
    TRANSCODE_720P_DONE = "TRANSCODE_720P_DONE"
    UPLOAD_FINISHED = "UPLOAD_FINISHED"

class VideoEvent(Base):
    __tablename__ = "processing_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transcode_job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transcode_jobs.id"))
    transcode_job: Mapped["TranscodeTask"] = relationship("TranscodeTask")

    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    # Many upload sessions -> one video
    video: Mapped["Video"] = relationship("Video")

    event_type: Mapped[VideoEventEnum] = mapped_column(Enum(VideoEventEnum), nullable=False, default=VideoEventEnum.NOT_STARTED.value)

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
        return f"<VideoEvent(id={self.id}, transcode_job_id={self.transcode_job_id}, \
             video_id={self.video_id}, event_type={self.event_type.value})>"
    

class RenditionTypeEnum(enum.Enum):
    HLS = "hls"
    DASH = "dash"
    # MP4 = "mp4"

class Rendition(Base):
    __tablename__ = "renditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    video: Mapped["Video"] = relationship("Video")
    
    type: Mapped[RenditionTypeEnum] = mapped_column(Enum(RenditionTypeEnum), nullable=False, default=RenditionTypeEnum.HLS)  # hls / dash / mp4
    resolution: Mapped[str] = mapped_column(String)  # 360p / 720p / 1080p

    object_key: Mapped[str] = mapped_column(String)  # R2 path
    # url is the public URL to access the rendition, which can be constructed using
    # the object_key and R2 bucket URL, but we can also store it here for easy access
    url: Mapped[str] = mapped_column(String)

    bitrate: Mapped[int] = mapped_column(Integer)

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
        return f"<Rendition(id={self.id}, video_id={self.video_id}, type={self.type.value}, resolution={self.resolution})>"
    