import uuid
from fastapi.routing import APIRouter
from fastapi import Depends, File, Form, UploadFile
import logging

from app.repositories.category_repository import CategoryRepository

from app.schemas import category_schema
from app.dependencies import get_current_user, get_category_repository, get_category_service
from app.services.category_service import CategoryService
from app.core.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/category", tags=["category"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=category_schema.CategoryOut, status_code=201)
async def create_new_category(
    name: str = Form(...),
    image: UploadFile | None = File(None),
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.create(name, image)


@router.get("/", response_model=list[category_schema.CategoryOut])
async def get_category_list(category_repo: CategoryRepository = Depends(get_category_repository)):
    return await category_repo.list()


@router.get("/{category_id}")
# @router.get("/{category_id}", response_model=category_schema.CategoryOut)
async def get_category_detail(category_id: uuid.UUID, category_service: CategoryService = Depends(get_category_service)):
    return await category_service.get_category_detail(category_id)
  

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