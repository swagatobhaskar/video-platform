from uuid import UUID
from datetime import datetime, UTC

from app.repositories.video_repository import VideoRepository
from app.models import Video, VideoPublicationStatusEnum
from app.exceptions.video import VideoPublishError
from app.core.database import AsyncSession


class VideoService:
    def __init__(self, session: AsyncSession, video_repository: VideoRepository):
        self.session = session
        self.video_repository = video_repository


    async def publish(self, video_id: UUID):
        video = self.video_repository.get(video_id)

        # Need video manager here
        if not video.can_publish:
            # raise ValueError(f"Video cannot be published: {self.publish_errors}")
            raise VideoPublishError(self.publish_errors)

        self.video.publication_status = VideoPublicationStatusEnum.PUBLISHED
        self.video.published_at = datetime.now(UTC)

        # VideoManager wont commit
        #
        # try:
        #     await self.session.commit()
        #     await self.session.refresh(self.video)
        # except SQLAlchemyError:
        #     await self.session.rollback()
        #     logger.exception("Database Error. Video publish failed!")
        #     raise # HTTPException(status_code=500, detail="Failed to publish video.")
