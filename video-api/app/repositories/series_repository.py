import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Series, Video
from app.core.database import AsyncSession


class SeriesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[Series]:
        result = await self.session.execute(select(Series))
        return result.scalars().all()

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
                selectinload(Series.videos).load_only(Video.id, Video.title, Video.episode_number)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, name: str) -> Series:
        series = Series(name=name)
        self.session.add(series)
        await self.session.flush()
        return series

    async def delete(self, series: Series) -> None:
        await self.session.delete(series)

    async def update(self, id:uuid.UUID, name: str) -> Series:
        series = await self.get(id)

        if not series:
            return None

        series.name = name

        await self.session.flush()

