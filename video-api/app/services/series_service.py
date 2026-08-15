from app.repositories.series_repository import SeriesRepository
from app.repositories.video_repository import VideoRepository

class SeriesService:
    def __init__(self, series_repo: SeriesRepository):
        self.series_repo = series_repo

    async def 