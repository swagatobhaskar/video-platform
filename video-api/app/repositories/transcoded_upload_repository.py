from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.database import AsyncSession
from app.models.upload import TranscodedUploadFile, TranscodedUploadSession, TranscodedUploadStatusEnum

class TranscodedUploadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, video_id: UUID) -> TranscodedUploadSession:
        transcoded_upload_session = TranscodedUploadSession(
            video_id=video_id,
            status=TranscodedUploadStatusEnum.PENDING,
        )
        self.session.add(transcoded_upload_session)
        await self.session.flush()
        return transcoded_upload_session


    async def get(self, transcoded_upload_session_id: UUID) -> TranscodedUploadSession | None:
        result = await self.session.execute(
            select(TranscodedUploadSession).where(
                TranscodedUploadSession.id == transcoded_upload_session_id
            )
        )
        return result.scalar_one_or_none()


    async def get_by_video(self, transcoded_upload_session_id: UUID, video_id: UUID) -> TranscodedUploadSession | None:
        result = await self.session.execute(
            select(TranscodedUploadSession).where(
                TranscodedUploadSession.id == transcoded_upload_session_id,
                TranscodedUploadSession.video_id == video_id
            )
        )
        return result.scalar_one_or_none()


    async def update_upload_session_status(self, transcoded_upload_session_id: UUID, video_id: UUID, status: TranscodedUploadStatusEnum) -> None:
        transcoded_upload_session = await self.get_by_video(transcoded_upload_session_id, video_id)

        if transcoded_upload_session:
            transcoded_upload_session.status = status
            
            if status == TranscodedUploadStatusEnum.COMPLETED:
                transcoded_upload_session.completed_at = datetime.now(timezone.utc)
                await self.session.flush()

    async def update(self, transcoded_upload_session_id: UUID, **data) -> TranscodedUploadSession | None:
        """Generic field update, used by pause/resume/complete: update(upload.id, status=..., completed_at=...)."""
        transcoded_upload_session = await self.get(transcoded_upload_session_id)

        if transcoded_upload_session is None:
            return None

        for field, value in data.items():
            setattr(transcoded_upload_session, field, value)

        await self.session.flush()
        return transcoded_upload_session

    async def get_file_by_path(self, transcoded_upload_session_id: UUID, relative_path: str) -> TranscodedUploadFile | None:
        result = await self.session.execute(
            select(TranscodedUploadFile).where(
                TranscodedUploadFile.transcoded_upload_session_id == transcoded_upload_session_id,
                TranscodedUploadFile.relative_path == relative_path,
            )
        )
        return result.scalar_one_or_none()
    

    async def create_file(
        self, *, upload_session_id: UUID, client_file_id: str,
        relative_path: str, object_key: str, size_bytes: int, content_type: str,
    ) -> TranscodedUploadFile:
        """
        Creates the file row and bumps the session's total_files/total_bytes
        counters (needed for get_status to report anything meaningful).
        Uses a savepoint so that if two concurrent presign-batch calls race on
        the same (session, relative_path) unique constraint, only this one
        insert is rolled back -- not the whole request's transaction, which
        may already contain other newly-created file rows from earlier in the
        same batch that haven't been committed yet.
        """
        try:
            async with self.session.begin_nested():
                upload_file = TranscodedUploadFile(
                    transcoded_upload_session_id=upload_session_id,
                    client_file_id=client_file_id,
                    relative_path=relative_path,
                    object_key=object_key,
                    size_bytes=size_bytes,
                    content_type=content_type,
                    status="PENDING",
                )
                self.session.add(upload_file)
                await self.session.flush()
        except IntegrityError:
            existing = await self.get_file_by_path(upload_session_id, relative_path)
            if existing is None:
                raise
            return existing

        transcoded_upload_session = await self.get(upload_session_id)
        if transcoded_upload_session:
            transcoded_upload_session.total_files += 1
            transcoded_upload_session.total_bytes += size_bytes
            await self.session.flush()

        return upload_file


    async def get_files(self, transcoded_upload_session_id: UUID) -> list[TranscodedUploadFile]:
        result = await self.session.execute(
            select(TranscodedUploadFile).where(
                TranscodedUploadFile.transcoded_upload_session_id == transcoded_upload_session_id
            )
        )
        return list(result.scalars().all())


    async def get_file_by_client_id(self, transcoded_upload_session_id: UUID, client_file_id: str) -> TranscodedUploadFile | None:
        result = await self.session.execute(
            select(TranscodedUploadFile).where(
                TranscodedUploadFile.transcoded_upload_session_id == transcoded_upload_session_id,
                TranscodedUploadFile.client_file_id == client_file_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_file_uploaded(self, transcoded_upload_file_id: UUID) -> None:
        upload_file = await self.session.get(TranscodedUploadFile, transcoded_upload_file_id)
        if upload_file:
            upload_file.status = "UPLOADED"
            upload_file.uploaded_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def increment_uploaded_files(self, transcoded_upload_session_id: UUID) -> None:
        transcoded_upload_session = await self.get(transcoded_upload_session_id)
        if transcoded_upload_session:
            transcoded_upload_session.uploaded_files_count += 1
            await self.session.flush()

    async def increment_uploaded_bytes(self, transcoded_upload_session_id: UUID, size_bytes: int) -> None:
        transcoded_upload_session = await self.get(transcoded_upload_session_id)
        if transcoded_upload_session:
            transcoded_upload_session.uploaded_bytes += size_bytes
            await self.session.flush()
