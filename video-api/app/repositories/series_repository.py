import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Series, Video
from app.core.database import AsyncSession
from app.repositories.video_repository import VideoRepository

class SeriesRepository:
    def __init__(self, session: AsyncSession, video_repo:VideoRepository):
        self.session = session
        self.video_repo = video_repo

    async def list(self) -> list[Series]:
        result = await self.session.execute(select(Series))
        return result.scalara().all()

    async def get(self, id: uuid.UUID):
        result = await self.session.execute(
            select(Series).where(Series.id == id)
        )
        return result.scalar_one_or_none()

    async def get_with_videos(self, id: uuid.UUID):
        result = await self.session.execute(
            select(Series)
            .where(Series.id == id)
            .options(
                selectinload(Series.videos).load_only(Video.id, Video.title)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, name: str) -> Series:
        series = Series(name=name)
        self.session.add(series)
        await self.session.flush()

    async def delete(self, id: uuid.UUID) -> None:
        series = await self.get(id)

        if not series:
            return None

        self.session.delete(series)

    async def update(self, id:uuid.UUID, name: str) -> Series:
        series = await self.get(id)

        if not series:
            return None

        series.name = name

        await self.session.flush()

    async def add_video(self, series_id: uuid.UUID, video_id: uuid.UUID) -> Series:
        series = await self.get(series_id)

        if not series:
            return None

        video = await self.video_repo.get(video_id)

        if not video:
            return None

        video.series = series

        await self.session.flush()

    async def remove_video(self, series_id: uuid.UUID, video_id: uuid.UUID) -> Series:
        series = await self.get(series_id)
        
        if not series:
            return None

        video = await self.video_repo.get(video_id)

        if not video:
            return None

        video.series != series

        await self.session.flush()
