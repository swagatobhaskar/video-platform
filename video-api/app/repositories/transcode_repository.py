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
    

    async def get(self, transcode_task_id: UUID) -> TranscodeTask | None:
        result = await self.session.execute(
            select(TranscodeTask).where(TranscodeTask.id == transcode_task_id)
        )
        return result.scalar_one_or_none()


    async def create(self, **data):
        transcode_task = TranscodeTask(**data)

        self.session.add(transcode_task)
        await self.session.flush()

        return transcode_task
    

    async def update(self, transcode_task_id: UUID, **data) -> TranscodeTask | None:
        transcode_task = await self.get(transcode_task_id)
        
        if transcode_task_id is None:
            return None

        for key, value in data.items():
            setattr(transcode_task, key, value)

        await self.session.flush()
        # the repository doesn't need to know about the rollback. The transaction handles it.
        return transcode_task
    """
    await transcode_repository.mark_started(
        task_id,
        celery_task_id=...,
        worker_id=...,
    )

    await transcode_repository.mark_downloading(
        task_id,
        progress=10,
    )

    await transcode_repository.mark_probing(
        task_id,
        progress=30,
    )

    await transcode_repository.mark_transcoding(
        task_id,
        progress=50,
    )

    await transcode_repository.mark_uploading(
        task_id,
        progress=70,
    )

    await transcode_repository.mark_completed(
        task_id,
    )

    await transcode_repository.mark_failed(
        task_id,
        error=str(exc),
    )
    """
    