from typing import List
import uuid
from datetime import datetime
import enum

from sqlalchemy import String, DateTime, func, Text, Enum, ForeignKey, Boolean
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
    

class LanguageEnum(enum.Enum):
    HINDI = "hindi"
    BENGALI = "bengali"

class Video(Base):
    __tablename__ = "videos"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum), nullable=False, default=LanguageEnum.BENGALI)
    
    seo_tags: Mapped[List[str]] = mapped_column(JSONB, nullable=True, default=list)
    
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    # Many videos -> one category
    category: Mapped["Category"] = relationship("Category", back_populates="videos")
    
    r2_video_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
    r2_thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
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
        return f"<Video(id={self.id}, title='{self.title}', language='{self.language.value}')>"
    
    
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
    
    r2_upload_url: Mapped[str] = mapped_column(String(255), nullable=False)
    
    r2_thumbnail_upload_url: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
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
    
    def __repr__(self) -> str:
        return f"<UploadSession(id={self.id}, video_id={self.video_id})>"
    

# pause/resume/retry; ETag, parts management
class VideoUploadAssets(Base):
    __tablename__ = "video_upload_assets"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # Many upload sessions -> one video
    video: Mapped["Video"] = relationship("Video")
    
    upload_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    
    part_number: Mapped[int] = mapped_column(nullable=False)
    
    etag: Mapped[str] = mapped_column(String(255), nullable=False)
    
    def __repr__(self) -> str:
        return f"<VideoUploadAssets(id={self.id}, video_id={self.video_id}, upload_session_id={self.upload_session_id})>"
    

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
    


class ProcessingEvent(Base):
    __tablename__ = "processing_events"
    
