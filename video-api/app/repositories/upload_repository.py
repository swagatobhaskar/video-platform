from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError, OperationalError

from app.database.models import UploadSession, UploadPart
from app.database.session import AsyncSession

class UploadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # NO BUSINESS LOGIC HERE. ONLY DB LEVEL NAMES AND OPERATIONS

    async def create(self, **data) -> UploadSession:
        upload_session = UploadSession(**data)

        try:
            self.session.add(upload_session)
            await self.session.flush() # refresh(upload_session) ?

        except SQLAlchemyError:
            # log
            await self.session.rollback()
            raise 

        return upload_session


    async def get(self, upload_session_id: UUID) -> UploadSession | None:
        result = await self.session.execute(
            select(UploadSession).where(UploadSession.id == upload_session_id)
        )
        return result.scalar_one_or_none()


    async def update(self, upload_session_id: UUID, **data) -> UploadSession | None:
        upload_session = await self.get(upload_session_id) # session.get(upload_session_id) ?

        if upload_session is None:
            return None

        for key, value in data.items():
            setattr(upload_session, key, value)

        try:
            await self.session.flush()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return upload_session


    async def delete(self, upload_session_id: UUID) -> bool:
        upload_session = await self.session.get(upload_session_id)

        if upload_session is None:
            return False

        try:
            await self.session.delete(upload_session)
            await self.session.flush()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return True


    async def create_part(self, **data) -> UploadPart:
        part = UploadPart(**data)

        try:
            self.session.add(part)
            await self.session.flush()
        except SQLAlchemyError:
            # log
            await self.session.rollback()
            raise 

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

        try:
            await self.session.flush()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return part
    