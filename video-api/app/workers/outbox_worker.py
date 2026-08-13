# the worker creates its own database session.
# Don't share your FastAPI request session with this process.

import asyncio

from app.core.database import AsyncSessionLocal
from app.repositories.outbox_repository import OutboxMessageRepository, OutboxProcessor
from app.repositories.transcode_repository import TranscodeRepository
# from app.workers.outbox_processor import OutboxProcessor


async def run_outbox_worker():
    while True:
        async with AsyncSessionLocal() as session:
            outbox_repository = OutboxMessageRepository(session)
            transcode_repository = TranscodeRepository(session)

            processor = OutboxProcessor(
                session=session,
                outbox_repository=outbox_repository,
                transcode_repository=transcode_repository
            )

            messages = await outbox_repository.claim_pending(limit=10)

            for message in messages:
                try:
                    await processor.process(message)
                except Exception as exc:
                    print(f"Failed processing outbox message {message.id}: {exc}")
                    # log

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_outbox_worker())
    