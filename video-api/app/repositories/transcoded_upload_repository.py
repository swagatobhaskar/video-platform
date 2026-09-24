
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

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select

from app.core.database import AsyncSession


class TranscodedUploadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_upload_session(self, video_id: UUID) -> TranscodedUploadSession:
        upload_session = TranscodedUploadSession(
            video_id=video_id,
            status=TranscodedUploadStatusEnum.PENDING,
        )
        self.session.add(upload_session)
        await self.session.flush()
        return upload_session


    async def get_upload_session(self, video_id: UUID) -> TranscodedUploadSession | None:
        result = await self.session.execute(
            select(TranscodedUploadSession).where(video_id=video_id)
        )
        return result.scalar_one_or_none()


    async def update_upload_session_status(self, video_id: UUID, status: TranscodedUploadStatusEnum) -> None:
        upload_session = await self.get_upload_session(video_id)

        if upload_session:
            upload_session.status = status
            
            if status == TranscodedUploadStatusEnum.COMPLETED:
                upload_session.completed_at = datetime.now(timezone.utc)
                await self.session.flush()

    async def update(self, ):
        pass

    async def get_file_by_path(self):
        pass

    async def create_file(self):
        pass

    async def get_files(self):
        pass

    async def get_for_video(self):
        pass

    async def get_file_by_client_id(self):
        pass

    async def mark_file_uploaded(self):
        pass

    async def increment_uploaded_files(self):
        pass

    async def increment_uploaded_bytes(self):
        pass

