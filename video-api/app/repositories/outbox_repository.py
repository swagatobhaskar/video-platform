from uuid import UUID
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from app.core.database import AsyncSession
from app.models import OutboxStatusEnum, OutboxMessage

class OutboxMessageRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_type: str, aggregate_type: str, aggregate_id: UUID, payload: dict) -> OutboxMessage:
        outbox_message = OutboxMessage(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status=OutboxStatusEnum.PENDING,
        )
        self.session.add(outbox_message)
        await self.session.flush()
        return outbox_message


    async def list(self) -> list[OutboxMessage]:
        result = await self.session.execute(select(OutboxMessage))
        return result.scalars().all()


    async def get(self, id: UUID) -> OutboxMessage | None:
            result = await self.session.execute(
                 select(OutboxMessage).where(OutboxMessage.id == id)
            )
            return result.scalar_one_or_none()


    async def update(self, id: UUID, **data):
        outbox_message = await self.get(id)

        if not outbox_message:
            return None

        for key, value in data.items():
            setattr(outbox_message, key, value)

        await self.session.flush()
        # the repository doesn't need to know about the rollback. The transaction handles it.
        return outbox_message


    async def get_pending(self, limit: int = 100): # -> list[OutboxMessage]:
        result = await self.session.execute(
            select(OutboxMessage)
            .where(
                OutboxMessage.status == OutboxStatusEnum.PENDING,
                OutboxMessage.available_at <= func.now(),
            )
            .order_by(OutboxMessage.created_at)
            .limit(limit)
        )

        # return list(result.scalars().all())
        return result.scalars().all()


    async def claim_pending(self, limit: int = 10) -> list[OutboxMessage]:
        result = await self.session.execute(
            select(OutboxMessage)
            .where(
                OutboxMessage.status == OutboxStatusEnum.PENDING,
                OutboxMessage.available_at <= func.now(),
            )
            .order_by(OutboxMessage.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        messages = list(result.scalars().all())

        for message in messages:
            message.status = OutboxStatusEnum.PROCESSING
            message.attempts += 1

        await self.session.commit()

        return messages


    async def mark_processing():
        pass

    async def mark_completed(self, message_id: UUID):
        message = await self.get(message_id)

        if message is None:
            return

        message.status = OutboxStatusEnum.COMPLETED
        message.processed_at = datetime.now(timezone.utc)

        await self.session.flush()


    async def mark_retry(self, message_id: UUID, error: str):
        message = await self.get(message_id)

        if message is None:
            return

        message.status = OutboxStatusEnum.PENDING
        message.last_error = error

        delay_seconds = min(300, 2 ** message.attempts)

        message.available_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        await self.session.flush()


    async def mark_failed(self, message_id: UUID, error: str):
        message = await self.get(message_id)

        if message is None:
            return

        message.status = OutboxStatusEnum.FAILED
        message.last_error = error

        await self.session.flush()

