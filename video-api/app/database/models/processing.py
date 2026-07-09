from typing import List
import uuid
from datetime import datetime
import enum

from sqlalchemy import (
    String, DateTime, func, Text, Enum, ForeignKey, Integer, Boolean
    )
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .video import Video
    from .upload import UploadSession

class VideoProcessingStatusEnum(enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"  # after file is sent to redis
    QUEUE_FAILED = "queue_failed"
    DOWNLOADING_VIDEO = "downloading_video"
    PROBING = "probing"
    TRANSCODING = "transcoding"
    UPLOADING = "uploading"
    CLEANUP = "cleanup"
    COMPLETED = "completed"
    FAILED = "failed"
    
class TranscodeTask(Base):
    __tablename__ = "transcode_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        
    # Many upload sessions -> one video
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)
    video: Mapped["Video"] = relationship("Video", back_populates="transcode_tasks")
        
    # Many upload sessions -> one video
    upload_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    upload_session: Mapped["UploadSession"] = relationship("UploadSession")

    status: Mapped[VideoProcessingStatusEnum] = mapped_column(
        Enum(VideoProcessingStatusEnum),
        nullable=False,
        default=VideoProcessingStatusEnum.PENDING
    )

    progress_percent: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    # Which worker machine/process is currently executing the job
    # though, required if you eventually run multiple dedicated transcoding machines.
    worker_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # The ID assigned by the queue system. Celery's unique ID for the task execution
    task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    
    events: Mapped[List["VideoEvent"]] = relationship("VideoEvent", back_populates="transcode_task")

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
    __tablename__ = "video_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transcode_task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transcode_tasks.id"), nullable=True)
    transcode_task: Mapped["TranscodeTask"] = relationship("TranscodeTask", back_populates="events")

    # Many events -> one video
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    video: Mapped["Video"] = relationship("Video", back_populates="video_events")

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, default="NOT_STARTED")
    # message: Mapped[str] = mapped_column(Text, nullable=True)
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
