from uuid import UUID
from sqlalchemy import select, update
from datetime import datetime, UTC

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


    async def create(self, **data) -> TranscodeTask:
        task = TranscodeTask(**data)
        self.session.add(task)
        await self.session.flush()
        return task
    

    async def update(self, transcode_task_id: UUID, **data) -> TranscodeTask | None:
        task = await self.get(transcode_task_id)
        
        if task is None:
            return None

        for key, value in data.items():
            setattr(task, key, value)

        await self.session.flush()
        return task


    async def claim(self, *, task_id: UUID, celery_task_id: str, worker_id: str) -> bool:
        """
        Atomically claim the transcode task.

        Returns:
            True  -> this worker successfully claimed it
            False -> another worker already claimed/completed it
        """
        now = datetime.now()

        stmt = (
            update(TranscodeTask)
            .where(
                TranscodeTask.id == task_id,
                TranscodeTask.status.in_(
                    [
                        VideoProcessingStatusEnum.PENDING,
                        VideoProcessingStatusEnum.QUEUED,
                    ]
                ),
            )
            .values(
                status=VideoProcessingStatusEnum.DOWNLOADING_VIDEO,
                task_id=celery_task_id,
                worker_id=worker_id,
                started_at=now,
                heartbeat_at=now,
                progress_percent=10,
                error_message=None,
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount == 1


    async def _update_progress(self, task_id: UUID, status: VideoProcessingStatusEnum, progress: int):
        await self.update(
            task_id,
            status=status,
            progress_percent=progress,
            heartbeat_at=datetime.now(UTC),
        )

        await self.session.commit()


    async def mark_downloading(self, task_id: UUID, progress: int =10) -> None:
        await self._update_progress(
            task_id,
            VideoProcessingStatusEnum.DOWNLOADING_VIDEO,
            progress,
        )


    async def mark_probing(self, task_id: UUID, progress: int = 30) -> None:
        await self._update_progress(
            task_id,
            VideoProcessingStatusEnum.PROBING,
            progress,
        )


    async def mark_transcoding(self, task_id: UUID, progress: int = 50) -> None:
        await self._update_progress(
            task_id,
            VideoProcessingStatusEnum.TRANSCODING,
            progress,
        )


    async def mark_uploading(self, task_id: UUID, progress: int = 70) -> None:
        await self._update_progress(
            task_id,
            VideoProcessingStatusEnum.UPLOADING,
            progress,
        )


    async def mark_cleanup(self, task_id: UUID, progress: int = 90) -> None:
        await self._update_progress(
            task_id,
            VideoProcessingStatusEnum.CLEANUP,
            progress,
        )


    async def mark_completed(self, task_id: UUID) -> None:
        now = datetime.now(UTC)

        await self.update(
            task_id,
            status=VideoProcessingStatusEnum.COMPLETED,
            progress_percent=100,
            finished_at=now,
            heartbeat_at=now,
            error_message=None,
        )

        await self.session.commit()


    async def mark_failed(self, task_id: UUID, error: str) -> None:
        now = datetime.now(UTC)

        await self.update(
            task_id,
            status=VideoProcessingStatusEnum.FAILED,
            error_message=error,
            finished_at=now,
            heartbeat_at=now,
        )

        await self.session.commit()

