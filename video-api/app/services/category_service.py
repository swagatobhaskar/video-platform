
from fastapi import UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool

from app.repositories.category_repository import CategoryRepository
from app.services.thumbnail_service import ThumbnailService

class CategoryService:
    def __init__(self, category_repo:CategoryRepository, thumbnail_service: ThumbnailService):
        self.category_repo = category_repo
        self.thumbnail_service = thumbnail_service


    async def create_new_category(self, image: UploadFile | None = File(None), name: str = Form(...)):
        image_key : str | None = None

        if image:
            # Validate the image
            await self.thumbnail_service.validate_image(image)
            # Convert the image to webp format
            webp_image = await self.thumbnail_service.convert(image)
            # Upload the image to R2 and get the image key
            image_key = await self.thumbnail_service.upload_thumbnail(webp_image)
        
        # Create a new category in the database with the provided name and image key
        new_category = await self.category_repo.create(name=name, image_url=image_key)
        return new_category
    