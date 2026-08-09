from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import AsyncSession
from app.models import TranscodeTask, VideoProcessingStatusEnum

class TranscodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[TranscodeTask]:
        result = await self.session.execute(select(TranscodeTask))
        return result.scalars().all()
    

    async def get(self, video_id: UUID) -> TranscodeTask | None:
        result = await self.session.execute(
            select(TranscodeTask).where(TranscodeTask.id == video_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **data):
        transcode_task = TranscodeTask(**data)

        try:
            self.session.add(transcode_task)
            await self.session.flush()

        except SQLAlchemyError:
            # log
            await self.session.rollback()
            raise

        return transcode_task
    

    async def update(self, transcode_task_id, **data):
        transcode_task = await self.session.get(transcode_task_id)
        
        if not transcode_task_id:
            return None

        for key, value in data.items():
            setattr(transcode_task_id, key, value)

        await self.session.flush()
        # the repository doesn't need to know about the rollback. The transaction handles it.
        return transcode_task