import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSession
from app.models import VideoTranscript, Video

class VideoTranscriptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: uuid.UUID):
        result = await self.session.execute(
            select(VideoTranscript).where(VideoTranscript.id == id)
        )

        return result.scalar_one_or_none()

    async def get_by_video_id(self, video_id: uuid.UUID):
        result = await self.session.execute(
            select(VideoTranscript).where(VideoTranscript.video_id == video_id)
        )

        return result.scalar_one_or_none()

    async def list(self):
        result = await self.session.execute(
            select(VideoTranscript)
        )

        return result.scalars().all()

    async def get_by_video(self, video_id: uuid.UUID):
        result = await self.session.execute(
            select(VideoTranscript).where(VideoTranscript.video_id == video_id)
        )
        # One video may have multiple transcipts
        return result.scalars().all()
    