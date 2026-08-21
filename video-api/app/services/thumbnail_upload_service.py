import uuid
from sqlalchemy.exc import SQLAlchemyError
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.repositories.video_repository import VideoRepository
from app.repositories.video_event_repository import VideoEventRepository
from app.exceptions.video import VideoNotFound, NoImageInRequest, ThumbnailAlreadyExists
from app.core.database import AsyncSession
from app.services.image_service import ImageProcessor
from app.storage.image_storage import ImageStorage

from app.core.config import get_settings
settings = get_settings()

class ThumbnailUploadService:
    def __init__(
        self,
        session: AsyncSession,
        video_repo: VideoRepository,
        image_processor: ImageProcessor,
        image_storage: ImageStorage,
        video_event_repo: VideoEventRepository,
    ):
        self.session = session
        self.video_repository = video_repo
        self.image_processor = image_processor
        self.image_storage = image_storage
        self.video_event_repo = video_event_repo

    async def upload(self, video_id: uuid.UUID, thumbnail_image: UploadFile):
        if not thumbnail_image:
            raise NoImageInRequest()
        
        video = await self.video_repository.get(video_id)

        if not video:
            raise VideoNotFound()

        if video.thumbnail_object_key:
            raise ThumbnailAlreadyExists() #(status_code=409, detail="Video already has a thumbnail.")

        await run_in_threadpool(self.image_processor.validate_image, thumbnail_image)

        # webp_buffer = self.image_processor.create_webp(thumbnail_image)
        webp_buffer = await run_in_threadpool(self.image_processor.create_webp, thumbnail_image)

        thumbnail_key: str | None = None

        try:
            key = f"{uuid.uuid4()}.webp"
            thumbnail_key = await run_in_threadpool(
                self.image_storage.upload,
                bucket=settings.thumbnails_bucket,
                img_buffer=webp_buffer,
                key=key,
            )

            await self.video_event_repo.create_video_event(
                video_id=video_id,
                event_type = "THUMBNAIL_UPLOADED_TO_R2",
                payload = {
                    "content_type": "image/webp",
                    "thumbnail_object_key": thumbnail_key,
                    "filename": thumbnail_image.filename,
                },
            )

            video.thumbnail_object_key = thumbnail_key
            await self.session.commit()

            return {
                "thumbnail_object_key": thumbnail_key,
            }
               
        except SQLAlchemyError:
            await self.session.rollback()
            # This avoids calling delete_object(Key=None) if the failure happened before the upload.
            if thumbnail_key is not None:
                # logger.exception("Database commit failed. Deleting uploaded thumbnail %s", thumbnail_key)
                await run_in_threadpool(
                    self.image_storage.delete,
                    thumbnail_key,
                    settings.thumbnails_bucket
                )
            raise


    async def update(self, video_id: uuid.UUID, thumbnail_image: UploadFile):
            
        if not thumbnail_image:
            raise NoImageInRequest()
            
        video = await self.video_repository.get(video_id)
    
        if not video:
            raise VideoNotFound()
    
        # First, upload the new image before deleting the old one
    
        await run_in_threadpool(self.image_processor.validate_image, thumbnail_image)
        
        webp_buffer = await run_in_threadpool(self.image_processor.create_webp, thumbnail_image)
    
        existing_thumbnail_key: str | None = video.thumbnail_object_key
        new_thumbnail_key: str | None = None
    
        try:
            key = f"{uuid.uuid4()}.webp"

            new_thumbnail_key = await run_in_threadpool(
                self.image_storage.upload,
                bucket=settings.thumbnails_bucket,
                img_buffer=webp_buffer,
                key=key,
            )
    
            # Save a new VIDEO_EVENT
            await self.video_event_repo.create_video_event(
                video_id=video_id,
                event_type = "THUMBNAIL_UPDATED",
                payload = {
                    "content_type": "image/webp",
                    "thumbnail_object_key": new_thumbnail_key,
                    "filename": thumbnail_image.filename,
                    "old_thumbnail_key": existing_thumbnail_key,
                },
            )
    
            video.thumbnail_object_key = new_thumbnail_key
            await self.session.commit()
    
            # Delete the older thumbnail
            if existing_thumbnail_key is not None:
                # logger.info("Deleting existing thumbnail from R2: %s", existing_thumbnail_key)
                await run_in_threadpool(
                    self.image_storage.delete,
                    existing_thumbnail_key,
                    settings.thumbnails_bucket
                )
    
            return {
                "thumbnail_object_key": new_thumbnail_key,
            }
    
        except SQLAlchemyError:
            await self.session.rollback()
    
            # This avoids calling delete_object(Key=None) if the failure happened before the upload.
            if new_thumbnail_key is not None:
                # logger.exception("Database commit failed. Deleting uploaded new thumbnail %s", new_thumbnail_key)
                await run_in_threadpool(
                    self.image_storage.delete,
                    new_thumbnail_key,
                    settings.thumbnails_bucket
                )
    
            raise 