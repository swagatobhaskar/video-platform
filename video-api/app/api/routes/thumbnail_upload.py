import logging
import uuid
from fastapi import APIRouter, Depends, File, UploadFile

from app.services.thumbnail_upload_service import ThumbnailUploadService
from app.dependencies import get_thumbnail_upload_service

router = APIRouter(prefix="/api/thumbnail", tags=["thumbnail",])

logger = logging.getLogger(__name__)


@router.post("/video/{video_id}/upload", status_code=201)
async def upload_video_thumbnail(
    video_id: uuid.UUID,
    thumbnail_image: UploadFile = File(),
    thumbnail_upload_service: ThumbnailUploadService = Depends(get_thumbnail_upload_service)
):
    return await thumbnail_upload_service.upload(video_id, thumbnail_image)


@router.patch("/video/{video_id}/upload")
async def change_video_thumbnail(
    video_id: uuid.UUID,
    thumbnail_image: UploadFile = File(),
    thumbnail_upload_service: ThumbnailUploadService = Depends(get_thumbnail_upload_service),
):
    return await thumbnail_upload_service.update(video_id, thumbnail_image)
