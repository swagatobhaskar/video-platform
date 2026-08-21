# the worker creates its own database session.
# Don't share your FastAPI request session with this process.

import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.repositories.outbox_repository import OutboxMessageRepository
from app.workers.outbox_processor import OutboxProcessor
from app.repositories.transcode_repository import TranscodeRepository

logger = logging.getLogger(__name__)

async def run_outbox_worker():
    while True:
        try:
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
                    except Exception:
                        # print(f"Failed processing outbox message {message.id}: {exc}")
                        logger.exception("Failed processing outbox message %s", message.id)
                        await session.rollback()

                        await outbox_repository.mark_retry(
                            message.id,
                            error="Unexpected outbox processing error",
                        )
                        await session.commit()
        except Exception:
            logger.exception("Outbox worker iteration failed")
            
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_outbox_worker())
    