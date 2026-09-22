from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
import kombu
import redis

from app.core.database import AsyncSession
from app.models import VideoProcessingStatusEnum, OutboxMessage
from app.repositories.outbox_repository import (
    OutboxMessageRepository,
)
from app.repositories.transcode_repository import (
    TranscodeRepository,
)
from app.tasks.transcode.transcode_task import (
    process_video_worker_operations,
)

class OutboxProcessor:

    def __init__(
        self,
        session: AsyncSession,
        outbox_repository: OutboxMessageRepository,
        transcode_repository: TranscodeRepository
    ):
        self.session = session
        self.outbox_repository = outbox_repository
        self.transcode_repository = transcode_repository

    async def process(self, message):
        if message.event_type != "VIDEO_TRANSCODE_REQUESTED":
            raise ValueError(f"Unknown outbox event: {message.event_type}")

        payload = message.payload

        try:
            task = process_video_worker_operations.delay(
                object_key=payload["object_key"],
                video_id=payload["video_id"],
                upload_id=payload["upload_id"],
                upload_session_id=payload["upload_session_id"],
                transcode_task_id=payload["transcode_task_id"],
            )
        except (
            redis.exceptions.ConnectionError,
            kombu.exceptions.OperationalError,
            RuntimeError,
        ) as exc:
            await self.outbox_repository.mark_retry(message.id, error=str(exc))
            await self.session.commit()
            # logger.exception("Failed to publish outbox message")
            return

        # Celery accepted the task.
        try:
            await self.transcode_repository.update(
                UUID(payload["transcode_task_id"]),
                status=VideoProcessingStatusEnum.QUEUED,
                task_id=str(task.id),
            )

            await self.outbox_repository.mark_completed(message.id)
            await self.session.commit()

        except SQLAlchemyError:
            await self.session.rollback()
            # logger.exception("Celery task was published but database state could not be updated")
            raise