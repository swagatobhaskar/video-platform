import uuid

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.database import AsyncSession
from app.models import Series
from app.repositories.series_repository import SeriesRepository
from app.repositories.video_repository import VideoRepository
from app.exceptions.series import SeriesNotFound, SeriesAlreadyExists, VideoAlreadyInTheSeries
from app.exceptions.video import VideoNotFound

class SeriesService:
    def __init__(self, series_repo: SeriesRepository, session: AsyncSession, video_repo: VideoRepository):
        self.series_repo = series_repo
        self.video_repo = video_repo
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


    async def update(self, id: uuid.UUID, name: str):
        series = await self.series_repo.get(id)

        if not series:
            raise SeriesNotFound

        if name is not None:
            series.name = name

        try:
            await self.session.commit()
            await self.session.refresh(series)  # added since returning updated_at requires a db refresh
        except IntegrityError:
            await self.session.rollback()
            raise SeriesAlreadyExists()
        except SQLAlchemyError:
            raise

        return series


    async def delete(self, id: uuid.UUID, delete_videos: bool = False) -> None:
        """
        You need to decide what should happen:
        > delete the videos automatically via SQLAlchemy/database cascade
        > set series_id to NULL
        > reject deletion if videos exist
        > detach/move the videos somewhere else
        """
        if delete_videos:
            series = await self.series_repo.get_with_videos(id)
        else:
            series = await self.series_repo.get(id)

        if not series:
            raise SeriesNotFound()

        try:
            if delete_videos:
                for video in series.videos:
                    await self.video_repo.delete(video)

            await self.series_repo.delete(series)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def add_video_to_series(self, series_id: uuid.UUID, video_id: uuid.UUID, episode_number: int):
        series = await self.series_repo.get(series_id)

        if not series:
            raise SeriesNotFound()

        video = await self.video_repo.get(video_id)

        if not video:
            raise VideoNotFound()

        video.series = series
        
        # Need to check the logic
        if episode_number:
            video.episode_number = episode_number

        try:
            await self.session.commit()
        except IntegrityError:
            raise VideoAlreadyInTheSeries
        except SQLAlchemyError:
            raise

        return await self.series_repo.get_with_videos(series_id)

    async def remove_video_from_series(self, series_id: uuid.UUID, video_id: uuid.UUID):
        series = await self.series_repo.get(series_id)

        if not series:
            raise SeriesNotFound()

        video = await self.video_repo.get(video_id)

        if not video:
            raise VideoNotFound()

        video.series != series

        try:
            await self.session.commit()
        except IntegrityError:
            raise VideoAlreadyInTheSeries
        except SQLAlchemyError:
            raise

        return await self.series_repo.get_with_videos(series_id)
    