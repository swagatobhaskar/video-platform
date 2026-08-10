from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError, OperationalError

from app.exceptions.upload import (
    UploadNotFound, UploadServiceError,
    NewUploadCreationFailed, UploadAlreadyCompleted,
    InvalidUploadState
)
from app.models import UploadSession, UploadPart
from app.core.database import AsyncSession

class UploadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # NO BUSINESS LOGIC HERE. ONLY DB LEVEL NAMES AND OPERATIONS

    async def create(self, **data) -> UploadSession:
        upload_session = UploadSession(**data)

        # try:
        self.session.add(upload_session)
        await self.session.flush()

        # except SQLAlchemyError:
            # log
            # await self.session.rollback()  # Do not rollback inside the repository.
            # raise NewUploadCreationFailed()

        return upload_session


    async def get(self, upload_session_id: UUID, video_id: UUID | None = None) -> UploadSession | None:
        if not video_id:
            result = await self.session.execute(
                select(UploadSession).where(UploadSession.id == upload_session_id)
            )
        else:
            result = await self.session.execute(
                select(UploadSession).where(UploadSession.video_id == video_id)
            )
        return result.scalar_one_or_none()


    async def get_for_video(self, upload_session_id: UUID, video_id: UUID) -> UploadSession | None:
        result = await self.session.execute(
            select(UploadSession).where(
                UploadSession.id == upload_session_id,
                UploadSession.video_id == video_id,
            )
        )

        return result.scalar_one_or_none()


    async def mark_upload_in_progress(
        self,
        upload_session: UploadSession,
        *,
        object_key: str,
        video_upload_id: str,
        file_size_bytes: int,
        mime_type: str,
        original_filename: str,
        total_parts: int,
    ):
        pass


    async def update(self, upload_session_id: UUID, **data) -> UploadSession | None:
        upload_session = await self.get(upload_session_id) # session.get(upload_session_id) ?

        if upload_session is None:
            return None

        for key, value in data.items():

            # if key == upload_session.uploaded_parts_count:
            #     setattr(upload_session, key, upload_session.uploaded_parts_count += 1)
                
            setattr(upload_session, key, value)

        # try:
        await self.session.flush()
        # except SQLAlchemyError:
        #     await self.session.rollback()
        #     raise 

        return upload_session


    async def delete(self, upload_session_id: UUID) -> bool:
        upload_session = await self.session.get(upload_session_id)

        if upload_session is None:
            return False

        # try:
        await self.session.delete(upload_session)
        await self.session.flush()
        # except SQLAlchemyError:
        #     await self.session.rollback()
        #     raise

        return True


    async def create_part(self, **data) -> UploadPart:
        part = UploadPart(**data)

        # try:
        self.session.add(part)
        await self.session.flush()
        # except SQLAlchemyError:
        #     # log
        #     await self.session.rollback()
        #     raise 

        return part


    async def get_part(self, upload_part_id: UUID) -> UploadPart | None:
        result = await self.session.execute(
            select(UploadPart).where(UploadPart.id == upload_part_id)
        )
        return result.scalar_one_or_none()


    async def update_parts(self, upload_part_id: UUID, **data) -> UploadPart | None:
        part = await self.get_part(upload_part_id)

        if part is None:
            return None

        for key, value in data.items():
            setattr(part, key, value)

        # try:
        await self.session.flush()
        # except SQLAlchemyError:
        #     await self.session.rollback()
        #     raise

        return part
    