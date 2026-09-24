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
if TYPE_CHECKING:
    from .video import Video


class UploadSessionStatusEnum(enum.Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # one upload sessions -> one video
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False) # nullable=True)
    video: Mapped["Video"] = relationship("Video", back_populates="upload_session")
    object_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_upload_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # What the user uploaded
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # optional, can be calculated after upload is complete using ETags of all parts/chunks and stored in videos table
    # checksum: Mapped[str] = mapped_column(String(255), nullable=True)

    # total number of parts/chunks the video is divided into for multipart upload
    total_parts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # number of parts/chunks successfully uploaded so far
    uploaded_parts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # One upload session -> many upload parts
    parts: Mapped[List["UploadPart"]] = relationship("UploadPart", back_populates="upload_session", cascade="all, delete-orphan")
    
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

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        return f"<UploadPart(id={self.id}, upload_session_id={self.upload_session_id})>"

class TranscodedUploadStatusEnum(str, Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class TranscodedUploadSession(Base):
    __tablename__ = "transcoded_upload_sessions"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    video_id: Mapped[UUID] = mapped_column(ForeignKey("videos.id"), nullable=False, unique=True)
    status: Mapped[TranscodedUploadStatusEnum] = mapped_column(
        Enum(TranscodedUploadStatusEnum), nullable=False, default=TranscodedUploadStatusEnum.PENDING
    )
    total_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_files_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    uploaded_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None]

        
    def __repr__(self) -> str:
        return f"<TranscodedUploadSession(id={self.id}, video_id={self.video_id})>"

class TranscodedUploadFile(Base):
    __tablename__ = "transcoded_upload_files"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcoded_upload_session_id: Mapped[UUID] = mapped_column(ForeignKey("transcoded_upload_sessions.id"), nullable=False)
    client_file_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    uploaded_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint(
        "upload_session_id",
        "relative_path",
        name="uq_transcoded_upload_file_path",
    ))

    def __repr__(self) -> str:
        return f"<TranscodedUploadSession(id={self.id}, transcoded_upload_session_id={self.transcoded_upload_session_id})>"
    