import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.schemas import category_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, Category
from app.config import get_settings

router = APIRouter(prefix="/api/category", tags=["category"])

settings = get_settings()


@router.post("/", response_model=category_schema.CategoryOut, status_code=201)
async def create_new_category(
    req: category_schema.CategoryCreate,
    session: AsyncSession = Depends(get_db)
):
    try:
        new_category = Category(**req.model_dump())
        session.add(new_category)
        await session.commit()
        await session.refresh(new_category)

    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="A category with that name already exists.")

    except SQLAlchemyError:
        await session.rollback()
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
    try:
        category = await session.get(Category, category_id)

        if category is None:
            raise HTTPException(404, "Category not found")

        await session.delete(category)
        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(500, "Database error")


@router.patch("/{category_id}", response_model=category_schema.CategoryOut)
async def update_category(
    category_id: uuid.UUID,
    req: category_schema.CategoryUpdate,
    session: AsyncSession = Depends(get_db),
):
    category = await session.get(Category, category_id)

    if category is None:
        raise HTTPException(404, "Category not found")

    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    try:
        await session.commit()
        await session.refresh(category)

    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Category name already exists")

    return category


# Add a video to a category
@router.post("/{category_id}/videos/{video_id}", response_model=category_schema.CategoryOut)
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
        .options(selectinload(Category.videos))
        .where(Category.id == category_id)
    )

    return result.scalar_one()


# Remove video from a category
@router.delete("/{category_id}/videos/{video_id}", response_model=category_schema.CategoryOut)
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
        .options(selectinload(Category.videos))
        .where(Category.id == category_id)
    )

    return result.scalar_one()
