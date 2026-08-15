import uuid
from typing import BinaryIO
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from app.core.database import AsyncSession

from app.repositories.category_repository import CategoryRepository
from app.repositories.video_repository import VideoRepository
from app.services.storage.image_service import ImageProcessor, ImageStorage
from app.exceptions.category import CategoryAlreadyExists, CategoryNotFound, VideoAlreadyLinked
from app.exceptions.video import VideoNotFound

from app.core.config import get_settings
settings = get_settings()


class CategoryService:
    def __init__(
        self,
        session: AsyncSession,
        category_repo: CategoryRepository,
        image_processor: ImageProcessor,
        image_storage: ImageStorage,
        video_repo: VideoRepository
    ):
        self.session = session
        self.category_repo = category_repo
        self.image_processor = image_processor
        self.image_storage = image_storage
        self.video_repo = video_repo

    BUCKET = settings.category_image_bucket

    # async def create(self, image: UploadFile | None = File(None), name: str = Form(...)):
    # async def create(self, name: str, image: BinaryIO | None = None):
    async def create(self, name: str, image: UploadFile | None = None):
        image_key : str | None = None

        if image:
            # Validate the image
            # await self.image_service.validate_image(image)
            await run_in_threadpool(self.image_service.validate_image, image)
            # Convert the image to webp format
            # webp_image = await self.image_service.create_webp(image)
            webp_image = await run_in_threadpool(self.image_service.create_webp, image)
            # Upload the image to R2 and get the image key
            # image_key = await self.image_storage.upload(webp_image)
            key = f"{uuid.UUID4()}.webp"
            image_key = await run_in_threadpool(self.image_storage.upload, key, self.BUCKET, webp_image) # key, bucket, img_buffer

        try:
            # Create a new category in the database with the provided name and image key
            new_category = await self.category_repo.create(name=name, image_url=image_key)
            await self.session.commit()
            return new_category
        except IntegrityError:
            await self.session.rollback()
            # logger.exception("Failed creating category '%s'", name)

            # Consider implementing Outbox or state machine approach to cleanup, cause the follwong step may fail also
            if image_key:
                await run_in_threadpool(self.image_storage.delete, image_key, self.BUCKET)

            raise CategoryAlreadyExists()

        except SQLAlchemyError:
            await self.session.rollback()
            if image_key is not None:
                # logger.exception("Database commit failed. Deleting uploaded category image %s", image_key)
                await run_in_threadpool(self.image_storage.delete, image_key, self.BUCKET)
                
            # raise HTTPException(status_code=500, detail="Database error.")
            raise 


    async def get_category_detail(self, id: uuid.UUID):
        category = await self.category_repo.get_with_videos(id)

        if not category:
            raise CategoryNotFound()

        return {
            "id": category.id,
            "name": category.name,
            "r2_category_image_key": category.r2_category_image_key,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "videos": [
                {
                    "id": video.id,
                    "title": video.title,
                }
                for video in category.videos
            ],
        }


    async def delete(self, id:uuid.UUID) -> None:
        # get the category
        category = await self.category_repo.get(id)

        if not category:
            raise CategoryNotFound()

        image_key = category.image_url

        try:
            await self.category_repo.delete(id)
        except SQLAlchemyError:
            # log
            raise

        # delete the image from storage
        if image_key:
            await run_in_threadpool(self.image_storage.delete, image_key, self.BUCKET)


    async def update(self, id: uuid.UUID, name: str | None, image: BinaryIO | None = None):
        category = await self.category_repo.get(id)

        if not category:
            return CategoryNotFound()

        if name is not None:
                category.name = name
        
        old_image_key = category.image_url
        new_image_key: str | None = None
    
        if image:
            # Early rejection only. It can't prevent files hidden as an image
            if not image.content_type.startswith("image/"):
                # raise HTTPException(400, "File must be an image.")
                raise
    
            # validate image
            await run_in_threadpool(self.image_processor.validate_image, image)
        
            # Convert to WebP
            webp_buffer = await run_in_threadpool(self.image_processor.create_webp, image)
    
            new_image_key = await run_in_threadpool(self.image_storage.upload, webp_buffer, self.BUCKET)
    
            category.image_url = new_image_key

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            # logger.exception("Failed to delete orphaned new category image from R2: %s", new_image_key)
            if new_image_key:
                await run_in_threadpool(self.image_storage.delete, new_image_key, self.BUCKET)
            raise CategoryAlreadyExists()
        except SQLAlchemyError:
            await self.session.rollback()
            # logger.exception("Database error occurred. Deleting new category image from R2: %s", new_image_key)
            if new_image_key:
                await run_in_threadpool(self.image_storage.delete, new_image_key, self.BUCKET)
            raise

        # DB update succeeded, so remove the old image.
        if new_image_key and old_image_key:
            await run_in_threadpool(self.image_storage.delete, old_image_key, self.BUCKET)
            # logger.exception("Failed to delete orphaned old category image from R2: %s", old_image_key)
    
        return category


    async def add_video_to_category(self, categoy_id: uuid.UUID, video_id: uuid.UUID):
        category = await self.category_repo.get(categoy_id)

        if not category:
            raise CategoryNotFound()

        video = await self.video_repo.get(video_id)

        if not video:
            raise VideoNotFound()

        video.category = category

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            # raise HTTPException(409, "Integrity constraint violated")
            raise VideoAlreadyLinked()
        except SQLAlchemyError:
            await self.session.rollback()
            raise # HTTPException(500, "Database error")
    
        # get category with videos
        return await self.category_repo.get_with_videos(categoy_id)


    async def remove_video_from_category(self, categoy_id: uuid.UUID, video_id: uuid.UUID):
        category = await self.category_repo.get(categoy_id)

        if not category:
            raise CategoryNotFound()

        video = await self.video_repo.get(video_id)

        if not video:
            raise VideoNotFound()

        video.category = None

        try:
            await self.session.commit()
        # except IntegrityError:
        #     await self.session.rollback()
        #     # raise HTTPException(409, "Integrity constraint violated")

        except SQLAlchemyError:
            await self.session.rollback()
            raise # HTTPException(500, "Database error")
    
        # get category with videos
        return await self.category_repo.get_with_videos(categoy_id)
    