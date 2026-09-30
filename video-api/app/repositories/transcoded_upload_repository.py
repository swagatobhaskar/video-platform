from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select

from app.core.database import AsyncSession
from app.models.upload import TranscodedUploadFile, TranscodedUploadSession, TranscodedUploadStatusEnum

class TranscodedUploadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, video_id: UUID) -> TranscodedUploadSession:
        upload_session = TranscodedUploadSession(
            video_id=video_id,
            status=TranscodedUploadStatusEnum.PENDING,
        )
        self.session.add(upload_session)
        await self.session.flush()
        return upload_session


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
        upload_session = await self.get_by_video(transcoded_upload_session_id, video_id)

        if upload_session:
            upload_session.status = status
            
            if status == TranscodedUploadStatusEnum.COMPLETED:
                upload_session.completed_at = datetime.now(timezone.utc)
                await self.session.flush()

    async def update(self, **data):
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

