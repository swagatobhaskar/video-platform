import uuid
from pathlib import Path
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends, File, Form, UploadFile
# from fastapi.concurrency import run_in_threadpool
# from sqlalchemy import select
# from sqlalchemy.orm import selectinload
# from sqlalchemy.exc import SQLAlchemyError, IntegrityError
# from botocore.exceptions import ClientError
import logging

from app.repositories.category_repository import CategoryRepository

from app.schemas import category_schema
# from app.database.session import AsyncSession
from app.dependencies import get_current_user, get_category_repository, get_category_service
from app.services.category_service import CategoryService
from app.utils import security
# from app.models import Video, Category
from app.core.config import get_settings

# from app.utils.image_helper import (
#     convert_to_webp, delete_image_from_r2, validate_image,
#     upload_image_to_r2,
# )

router = APIRouter(prefix="/api/category", tags=["category"])

settings = get_settings()

logger = logging.getLogger(__name__)


# BUCKET = settings.category_image_bucket

@router.post("/", response_model=category_schema.CategoryOut, status_code=201)
async def create_new_category(
    name: str = Form(...),
    image: UploadFile | None = File(None),
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.create(name, image)

    """
    image_key : str | None = None

    if image:
        # validate_image(image)
        await run_in_threadpool(validate_image, image)

        # convert to webp
        # img_buffer = convert_to_webp(image)
        webp_buffer = await run_in_threadpool(convert_to_webp, image)

        # image_key: str = await upload_image_to_r2(webp_buffer, BUCKET)
        try:
            image_key = await run_in_threadpool(
                upload_image_to_r2,
                webp_buffer,
                BUCKET,
            )
        except ClientError:
            logger.exception("Failed to upload image")
            raise HTTPException(503, "Image upload failed")

    try:
        new_category = Category(name=name, image_url = image_key)
        session.add(new_category)
        await session.commit()
        await session.refresh(new_category)

    except IntegrityError:
        await session.rollback()
        logger.exception("Failed creating category '%s'", name)

        if image_key:
            logger.exception("Database commit aborted due to IntegrityError. Deleting uploaded category image %s", image_key)
            try:
                await run_in_threadpool(delete_image_from_r2, image_key, BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned category image from R2: %s", image_key)
        raise HTTPException(status_code=409, detail="A category with that name already exists.")

    except SQLAlchemyError:
        await session.rollback()

        if image_key is not None:
            logger.exception("Database commit failed. Deleting uploaded category image %s", image_key)

            try:
                await run_in_threadpool(delete_image_from_r2, image_key, BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned category image from R2: %s", image_key)
        raise HTTPException(status_code=500, detail="Database error.")

    return new_category
    """

@router.get("/", response_model=list[category_schema.CategoryOut])
async def get_category_list(category_repo: CategoryRepository = Depends(get_category_repository)):
    return await category_repo.list()


@router.get("/{category_id}")
# @router.get("/{category_id}", response_model=category_schema.CategoryOut)
async def get_category_detail(category_id: uuid.UUID, category_service: CategoryService = Depends(get_category_service)):
    return await category_service.get_category_detail(category_id)
    """
    result = await session.execute(
        select(Category)
        .options(selectinload(Category.videos).load_only(Video.id, Video.title))
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found!")

    # If using the schema based response
    # return category_schema.CategoryOut.model_validate(category)

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
    """


# Keep the videos, just remove their category.
@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: uuid.UUID, category_service: CategoryService = Depends(get_category_service)):
    return await category_service.delete(category_id)
    """
    category = await session.get(Category, category_id)

    if category is None:
        raise HTTPException(404, "Category not found")

    image_key = category.image_url

    try:
        await session.delete(category)
        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        logger.exception("Failed to delete category .")
        raise HTTPException(500, "Database error")

    # The database delete succeeded, so it's safe to delete the image.
    if image_key:
        try:
            await run_in_threadpool(delete_image_from_r2, image_key, BUCKET)
        except ClientError:
            logger.exception("Failed to delete orphaned category image from R2: %s", image_key)
    """

@router.patch("/{category_id}", response_model=category_schema.CategoryOut)
async def update_category(
    category_id: uuid.UUID,
    name: str | None = Form(None),
    image: UploadFile | None = File(None),
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.update(category_id, name, image)
    """
    category = await session.get(Category, category_id)

    if category is None:
        raise HTTPException(404, f"Category {name} not found")

    # for key, value in req.model_dump(exclude_unset=True).items():
    #     setattr(category, key, value)
    if name is not None:
        category.name = name

    old_image_key = category.image_url
    new_image_key: str | None = None

    if image:
        # Early rejection only. It can't prevent files hidden as an image
        if not image.content_type.startswith("image/"):
            raise HTTPException(400, "File must be an image.")

        # validate image
        await run_in_threadpool(validate_image, image)
    
        # Convert to WebP
        webp_buffer = await run_in_threadpool(convert_to_webp, image)

        # new_image_key = await upload_image_to_r2(image)
        try:
            new_image_key = await run_in_threadpool(
                upload_image_to_r2,
                webp_buffer,
                BUCKET,
            )
        except ClientError:
            logger.exception("Failed to upload image")
            raise HTTPException(503, "Image upload failed")

        category.image_url = new_image_key

    try:
        await session.commit()
        await session.refresh(category)

    except IntegrityError:
        await session.rollback()

        # Remove the newly-uploaded image because the DB update failed.
        if new_image_key:
            try:
                await run_in_threadpool(delete_image_from_r2, new_image_key, BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned new category image from R2: %s", new_image_key)

        raise HTTPException(409, "Category name already exists")

    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Database error occurred. Deleting new category image from R2: %s", new_image_key)

        if new_image_key:
            try:
                await run_in_threadpool(delete_image_from_r2, new_image_key, BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned new category image from R2: %s", new_image_key)

        raise HTTPException(500, "Database error")

    # DB update succeeded, so remove the old image.
    if new_image_key and old_image_key:
        try:
            await run_in_threadpool(delete_image_from_r2, old_image_key, BUCKET)
        except ClientError:
            logger.exception("Failed to delete orphaned old category image from R2: %s", old_image_key)

    return category
    """

# Add a video to a category
@router.post("/{category_id}/video/{video_id}", response_model=category_schema.CategoryOutWithVideo)
async def add_video_to_category(
    category_id: uuid.UUID,
    video_id: uuid.UUID,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.add_video_to_category(category_id, video_id)
    """
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(404, "Requested category not found")

    video = await session.get(Video, video_id)
    if video is None:
        raise HTTPException(404, "Requested video not found")

    if video.category_id is not None:
        raise HTTPException(status_code=409, detail="Video already belongs to a category.")

    video.category = category
    # or:
    # video.category_id = category.id
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Integrity constraint violated")
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(500, "Database error")

    # this doesn't match I think!
    result = await session.execute(
        select(Category)
        .options(selectinload(Category.videos).load_only(Video.id, Video.title))
        .where(Category.id == category_id)
    )

    return result.scalar_one()
    """

# Remove video from a category
@router.delete("/{category_id}/video/{video_id}", response_model=category_schema.CategoryOutWithVideo)
async def remove_video_from_category(
    category_id: uuid.UUID,
    video_id: uuid.UUID,
    category_service: CategoryService = Depends(get_category_service),
    # session: AsyncSession = Depends(get_db),
):
    return await category_service.remove_video_from_category(category_id, video_id)
    """
    category = await session.get(Category, category_id)

    if category is None:
        raise HTTPException(404, "Category not found")
    
    video = await session.get(Video, video_id)

    if video is None:
        raise HTTPException(404, "Video not found")

    if video.category_id != category_id:
        raise HTTPException(400, "Video is not in this category")

    # Remove relationship
    video.category = None
    # or:
    # video.category_id = None

    try:
        await session.commit()

    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Could not remove video from category")

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(500, "Database error")

    # Reload category with videos relationship populated
    result = await session.execute(
        select(Category)
        .options(selectinload(Category.videos).load_only(Video.id, Video.title))
        .where(Category.id == category_id)
    )

    return result.scalar_one()
    """