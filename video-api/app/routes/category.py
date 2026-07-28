import uuid
from pathlib import Path
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import mimetypes
import logging

from app.schemas import category_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, Category
from app.config import get_settings
from app.utils.r2_helper import s3

router = APIRouter(prefix="/api/category", tags=["category"])

settings = get_settings()

logger = logging.getLogger(__name__)

# Instead of using pre-signed url this time, the image is uploaded through the backend
async def upload_image_to_r2(image: UploadFile) -> str:
    # extension = image.filename.split(".")[-1]
    extension = Path(image.filename).suffix
    filename = f"{uuid.uuid4()}.{extension}"
    print("Ext, filename: ", extension, filename)

    s3.upload_fileobj(
        image.file,
        settings.category_image_bucket,
        filename,
        ExtraArgs={
            "ContentType": image.content_type,
        },
    )

    # return f"{settings.category_image_bucket_dev_url}/{filename}"
    print("filename after r2 upload: ", filename)
    return filename


async def delete_image_from_r2(object_key: str) -> None:
    await run_in_threadpool(s3.delete_object, Bucket=settings.category_image_bucket, Key=object_key)

async def safe_delete_from_r2(object_key: str) -> None:
    try:
        await delete_image_from_r2(object_key)
    except Exception:
        # Log the error; don't mask the original exception.
        logger.exception("Failed to delete orphaned R2 object: %s", object_key)

@router.post("/", response_model=category_schema.CategoryOut, status_code=201)
async def create_new_category(
    name: str = Form(...),
    image: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_db)
):
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB
    image_key : str | None = None

    if image and not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image.")

    # This is likely unreliable
    # if image and not image.size < MAX_SIZE:
    #     raise HTTPException(400, "Image size exceeds 5 MB.")

    if image:
        image_key = await upload_image_to_r2(image)

    try:
        new_category = Category(name=name, image_url = image_key)
        session.add(new_category)
        await session.commit()
        await session.refresh(new_category)

    except IntegrityError:
        await session.rollback()
        if image_key:
            await safe_delete_from_r2(image_key)
        raise HTTPException(status_code=409, detail="A category with that name already exists.")

    except SQLAlchemyError:
        await session.rollback()
        if image_key:
            await safe_delete_from_r2(image_key)
        raise HTTPException(status_code=500, detail="Database error.")

    return new_category
    

@router.get("/", response_model=list[category_schema.CategoryOut])
async def get_category_list(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Category))
    all_categories = result.scalars().all()
    return all_categories


@router.get("/{category_id}")
# @router.get("/{category_id}", response_model=category_schema.CategoryOut)
async def get_category_detail(category_id: uuid.UUID, session: AsyncSession = Depends(get_db)):

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
        "image_url": category.image_url,
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


# Keep the videos, just remove their category.
@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    
    category = await session.get(Category, category_id)

    if category is None:
        raise HTTPException(404, "Category not found")

    image_key = category.image_url

    try:
        await session.delete(category)
        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(500, "Database error")

    # The database delete succeeded, so it's safe to delete the image.
    if image_key:
        await safe_delete_from_r2(image_key)


@router.patch("/{category_id}", response_model=category_schema.CategoryOut)
async def update_category(
    category_id: uuid.UUID,
    name: str | None = Form(None),
    image: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_db),
):
    category = await session.get(Category, category_id)

    if category is None:
        raise HTTPException(404, "Category not found")

    # for key, value in req.model_dump(exclude_unset=True).items():
    #     setattr(category, key, value)
    if name is not None:
        category.name = name

    old_image_key = category.image_url
    new_image_key = None

    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(400, "File must be an image.")

        new_image_key = await upload_image_to_r2(image)
        category.image_url = new_image_key

    try:
        await session.commit()
        await session.refresh(category)

    except IntegrityError:
        await session.rollback()

        # Remove the newly-uploaded image because the DB update failed.
        if new_image_key:
            await safe_delete_from_r2(new_image_key)

        raise HTTPException(409, "Category name already exists")

    except SQLAlchemyError:
        await session.rollback()

        if new_image_key:
            await safe_delete_from_r2(new_image_key)

        raise HTTPException(500, "Database error")

    # DB update succeeded, so remove the old image.
    if new_image_key and old_image_key:
        await safe_delete_from_r2(old_image_key)

    return category


# Add a video to a category
@router.post("/{category_id}/video/{video_id}", response_model=category_schema.CategoryOutWithVideo)
async def add_video_to_category(
    category_id: uuid.UUID,
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):

    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(404, "Category not found")

    video = await session.get(Video, video_id)
    if video is None:
        raise HTTPException(404, "Video not found")

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


# Remove video from a category
@router.delete("/{category_id}/video/{video_id}", response_model=category_schema.CategoryOutWithVideo)
async def remove_video_from_category(
    category_id: uuid.UUID,
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
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
