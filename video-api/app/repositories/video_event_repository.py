from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import AsyncSession
from app.models import Video, VideoEvent

class VideoEventRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # pagination later
    async def list(self) -> list[VideoEvent]:
        result = await self.session.execute(select(VideoEvent))
        return result.scalars().all()
    

    async def get(self, video_event_id: UUID) -> VideoEvent | None:
        result = await self.session.execute(
            select(VideoEvent).where(VideoEvent.id == video_event_id)
        )
        return result.scalar_one_or_none()

    
    async def create_video_event(self, **data) -> VideoEvent:
        video_event = VideoEvent(**data)
        self.session.add(video_event)
        await self.session.flush()
        return video_event


    async def update(self, video_event_id: UUID, **data) -> VideoEvent | None:
        video_event = await self.get(video_event_id)

        if not video_event:
            return None

        for key, value in data.items():
            setattr(video_event, key, value)

        try:
            await self.session.flush()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return video_event


    async def delete(self, video_event: Video) -> None:
        await self.session.delete(video_event)

