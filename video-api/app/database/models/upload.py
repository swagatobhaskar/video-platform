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
if TYPE_CHECKING:
    from .video import Video


class UploadSessionStatusEnum(enum.Enum):
    # IDLE = "idle"
    PENDING = "pending"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Many upload sessions -> one video
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)
    video: Mapped["Video"] = relationship("Video", back_populates="upload_sessions")

    # object_key = “path in object storage” / what file in R2 this upload session is writing to / Where you store it in R2
    object_key: Mapped[str] = mapped_column(String(255), nullable=True)
    video_upload_id: Mapped[str] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[BigInteger] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=True)
    # What the user uploaded
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # optional, can be calculated after upload is complete using ETags of all parts/chunks and stored in videos table
    # checksum: Mapped[str] = mapped_column(String(255), nullable=True)

    # total number of parts/chunks the video is divided into for multipart upload
    total_parts: Mapped[int] = mapped_column(Integer, nullable=True)
    # number of parts/chunks successfully uploaded so far
    uploaded_parts_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    # One upload session -> many upload parts
    parts: Mapped[List["UploadPart"]] = relationship("UploadPart", back_populates="upload_session", cascade="all, delete-orphan")
    
    # Compute those from Video and related tables instead.
    # thumbnail_upload_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # metadata_complete: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    # video_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    # thumbnail_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    # transcript_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    
    status: Mapped[UploadSessionStatusEnum] = mapped_column(
        Enum(
            UploadSessionStatusEnum,
            # Tell SQLAlchemy to store the enum values (lowercase),
            # NOT UPPERCASE enum names.
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=UploadSessionStatusEnum.PENDING
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
    
    # Many upload parts -> one upload session
    upload_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    upload_session: Mapped["UploadSession"] = relationship("UploadSession", back_populates="parts")

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
    
