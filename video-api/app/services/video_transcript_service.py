import uuid

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import AsyncSession
from app.models import VideoTranscript
from app.exceptions.video_transcript import VideoTranscriptNotFound
from app.repositories.video_transcript_repository import VideoTranscriptRepository

class VideoTranscriptService:
    def __init__(self, video_transcript_repository: VideoTranscriptRepository, session: AsyncSession):
        self.video_transcript_repository = video_transcript_repository
        self.session = session

    async def list(self):
        return await self.video_transcript_repository.list()

    async def get(self, id: uuid.UUID):
        video_transcript = await self.video_transcript_repository.get(id)

        if not video_transcript:
            raise VideoTranscriptNotFound()

        return video_transcript
    