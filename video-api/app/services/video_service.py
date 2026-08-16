from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.domain.video_manager import VideoManager
from app.repositories.video_repository import VideoRepository
from app.models import Video, VideoPublicationStatusEnum
from app.exceptions.video import VideoPublishError, VideoNotFound, VideoArchiveFailed, DuplicateEntryError
from app.core.database import AsyncSession
from app.services.storage.r2_video_storage import R2VideoStorage
from app.services.storage.image_service import ImageStorage
from app.schemas.video_schema import VideoUploadHistoryRead, VideoMetadataUpdate, VideoSEOUpdate

from app.core.config import get_settings
settings = get_settings()

class VideoService:
    def __init__(
        self,
        session: AsyncSession,
        video_repository: VideoRepository,
        storage: R2VideoStorage,
        # manager: VideoManager should probably not be injected because the VideoManager is created for a particular Video
        # So you don't have a reusable manager instance to inject.
        # manager: VideoManager
    ):
        self.session = session
        self.video_repository = video_repository
        self.storage = storage
        # self.manager = manager


    async def publish(self, video_id: UUID):
        video = await self.video_repository.get_unpublished_video(video_id)

        if not video:
            raise VideoNotFound()

        manager = VideoManager(video)

        if not manager.can_publish:
            # raise ValueError(f"Video cannot be published: {self.publish_errors}")
            raise VideoPublishError(manager.publish_errors)

        # It can be done also, because you already have the entity. and let the service commit.:
        # video.publication_status = VideoPublicationStatusEnum.PUBLISHED
        # video.published_at = datetime.now(UTC)

        await self.video_repository.update(
            video_id,
            publication_status = VideoPublicationStatusEnum.PUBLISHED,
            published_at = datetime.now(UTC),
        )

        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            # logger.exception("Database Error. Video publish failed!")
            raise

        return video
        # A bare `raise` is correct. What does bare raise mean?
        #
        # Inside:
        # except SQLAlchemyError:
        #     await self.session.rollback()
        #     raise
        # bare raise means: Re-raise the exact exception that was caught.
        # So if SQLAlchemy throws: IntegrityError
        # you rollback and then propagate that same IntegrityError.
        #
        # It's equivalent conceptually to:
        # except SQLAlchemyError as exc:
        #     await self.session.rollback()
        #     raise exc
        # but bare raise is preferable because it preserves the original traceback more cleanly.

    async def update_transcript(self):
        pass

    async def update_seo(self):
        pass

    async def update_metadata(self):
        pass

    async def get_detail(self, id: UUID):
        video = await self.video_repository.get_video_detail(id)

        if not video:
            raise VideoNotFound()

        return video

    async def delete(self, id:UUID):
        video = await self.video_repository.get(id)

        if video is None:
            raise VideoNotFound()

        # Save these BEFORE deleting the ORM object.
        object_key = video.object_key
        thumbnail_key = video.thumbnail_object_key

        try:
            await self.video_repository.delete(video)
            # delete UploadSession and TranscodeTask records are handled by cascade delete in the ORM model.
            await self.session.commit()

        except SQLAlchemyError:
            await self.session.rollback()
            raise

        # Delete storage objects only after DB deletion succeeds.
        if object_key:
            self.storage.delete_video(object_key)

        if thumbnail_key:
            image_storage = ImageStorage()
            image_storage.delete(thumbnail_key, settings.thumbnails_bucket)
        """
        Eventually, this is a good candidate for an asynchronous cleanup job:

            VideoService.delete()
                │
                ├── DB delete + commit
                │
                └── enqueue "delete_video_storage"
                                ↓
                            Celery
                                ↓
                               R2

        That way, the user-facing delete operation is primarily concerned with the database transaction, while storage cleanup is reliable and retryable.
        """
        return {
            "message": "Video deleted successfully.",
            "video_id": str(id),
        }

    async def list(self, status: VideoPublicationStatusEnum | None = None):
        return await self.video_repository.list_videos(status)

    async def get_upload_history(self) -> list[VideoUploadHistoryRead]:
        videos = await self.video_repository.get_upload_history()

        return [
            VideoUploadHistoryRead(
                **VideoUploadHistoryRead.model_validate(video).model_dump(),
                video_status=video.upload_status,
                progress_percent=video.task_progress_percent
            ) for video in videos
        ]

    async def get_videos_requiring_user_action(self):
        drafts: list[Video] = await self.video_repository.get_drafts()

        response = []

        for video in drafts:
            manager = VideoManager(video)
            if manager.can_publish:
                continue

            response.append(
                {
                    "video_id": video.id,
                    "title": video.title,
                    "upload_status": manager.upload_status,
                    "transcoded": manager.transcoded,
                    "errors": manager.publish_errors,
                }
            )
    
        return response

    async def archive(self, id: UUID):
        video = await self.video_repository.get(id)

        if not video:
            raise VideoNotFound()
        
        archived = await self.video_repository.archive_video(id)

        if not archived:
            raise VideoArchiveFailed()

        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            # logger.exception("Database error. Failed to archive video %s", video_id)
            raise

        return {
            "message": "Video archived successfully.",
            "status": "archived",
        }

    async def get_admin_view(self, status: VideoPublicationStatusEnum | None = None):
        return await self.video_repository.get_for_admin(status)


    async def update_transcript(self, id:UUID):
        video = await self.video_repository.get_with_transcripts(id)

        if not video:
            raise VideoNotFound()


    async def update_metadata(self, id:UUID, req:VideoMetadataUpdate):
        video = await self.video_repository.get_for_metadata(id)

        if not video:
            raise VideoNotFound()

        # Without exclude_unset=True, you would accidentally overwrite existing values with NULL.
        update_data = req.model_dump(exclude_unset=True)
        
        try:
            await self.video_repository.update_data(update_data)
            return video
    
        except IntegrityError:
            await self.session.rollback()
            # raise HTTPException(status_code=400, detail="Invalid data. Update violates database constraints.")
            raise DuplicateEntryError()
    
        except SQLAlchemyError:
            await self.session.rollback()
            # logger.exception("Database error while updating video %s", video_id)
            raise

    async def update_seo(self, id:UUID, req:VideoSEOUpdate):
            video = await self.video_repository.get_for_seo(id)
    
            if not video:
                raise VideoNotFound()
    
            # Without exclude_unset=True, you would accidentally overwrite existing values with NULL.
            seo_data = req.model_dump(exclude_unset=True)
            
            try:
                await self.video_repository.update_data(seo_data)
                return video
        
            except SQLAlchemyError:
                await self.session.rollback()
                # logger.exception("Database error while updating video %s", video_id)
                raise
            