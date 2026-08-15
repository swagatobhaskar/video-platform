import uuid

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.database import AsyncSession
from app.models import Series
from app.repositories.series_repository import SeriesRepository
from app.repositories.video_repository import VideoRepository
from app.exceptions.series import SeriesNotFound, SeriesAlreadyExists, VideoAlreadyInTheSeries

class SeriesService:
    def __init__(self, series_repo: SeriesRepository, session: AsyncSession):
        self.series_repo = series_repo
        self.session = session

    async def list(self):
        return await self.series_repo.list()


    async def get_series_detail(self, id: uuid.UUID):
        series = await self.series_repo.get_with_videos(id)

        if not series:
            raise SeriesNotFound()

        return series


    async def create(self, name: str) -> Series:
        series = await self.series_repo.create(name)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise SeriesAlreadyExists()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        return series

    