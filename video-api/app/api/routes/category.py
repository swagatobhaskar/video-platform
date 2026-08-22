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
  

# Remove video from a category
@router.delete("/{category_id}/video/{video_id}", response_model=category_schema.CategoryOutWithVideo)
async def remove_video_from_category(
    category_id: uuid.UUID,
    video_id: uuid.UUID,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.remove_video_from_category(category_id, video_id)
