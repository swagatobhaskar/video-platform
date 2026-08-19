import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
# from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from botocore.exceptions import ClientError

from app.utils.image_helper import convert_to_webp, upload_image_to_r2, validate_image, delete_image_from_r2
from app.dependencies import get_db
from app.models import Video, VideoEvent
from app.core.database import AsyncSession

from app.core.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/thumbnail", tags=["thumbnail",])

logger = logging.getLogger(__name__)

THUMBNAIL_BUCKET = settings.thumbnails_bucket

@router.post("/video/{video_id}/upload", status_code=201)
async def upload_video_thumbnail(
    video_id: uuid.UUID,
    thumbnail_image: UploadFile = File(),
    session: AsyncSession = Depends(get_db),
):
    if not thumbnail_image:
        raise HTTPException(400, "Thumbnail image not found in request.")
    
    result = await session.execute(
        select(Video).where(Video.id == video_id)
    )

    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    if video.thumbnail_object_key:
        raise HTTPException(status_code=409, detail="Video already has a thumbnail.")

    # validate_image(thumbnail_image)
    await run_in_threadpool(validate_image, thumbnail_image)

    # webp_buffer = convert_to_webp(thumbnail_image)
    webp_buffer = await run_in_threadpool(convert_to_webp, thumbnail_image)

    thumbnail_key: str | None = None

    try:
        # thumbnail_key: str = upload_image_to_r2(webp_buffer, THUMBNAIL_BUCKET)
        thumbnail_key = await run_in_threadpool(
            upload_image_to_r2,
            webp_buffer,
            THUMBNAIL_BUCKET,
        )

        # Save a new VIDEO_EVENT
        video_event = VideoEvent(
            video_id=video_id,
            event_type = "THUMBNAIL_UPLOADED_TO_R2",
            payload = {
                "content_type": "image/webp",
                "thumbnail_object_key": thumbnail_key,
                "filename": thumbnail_image.filename,
            },
        )
        session.add(video_event)
        
        video.thumbnail_object_key = thumbnail_key

        await session.commit()

        return {
            "thumbnail_object_key": thumbnail_key,
        }

    except ClientError:
        # logger.exception() automatically includes the traceback
        logger.exception("Thumbnail upload failed for video %s", video_id)
        raise HTTPException(status_code=500, detail="S3 error.")

    except SQLAlchemyError:
        await session.rollback()

        # This avoids calling delete_object(Key=None) if the failure happened before the upload.
        if thumbnail_key is not None:
            logger.exception("Database commit failed. Deleting uploaded thumbnail %s", thumbnail_key)

            try:
                await run_in_threadpool(delete_image_from_r2, thumbnail_key, THUMBNAIL_BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned thumbnail from R2: %s", thumbnail_key)

        raise HTTPException(status_code=500, detail="Could not save thumbnail upload.")


@router.patch("/video/{video_id}/upload")
async def change_video_thumbnail(
    video_id: uuid.UUID,
    thumbnail_image: UploadFile = File(),
    session: AsyncSession = Depends(get_db),
):
    new_thumbnail_image = thumbnail_image
    
    if not new_thumbnail_image:
        raise HTTPException(400, "Thumbnail image not found in request.")
    
    result = await session.execute(
        select(Video).where(Video.id == video_id)
    )

    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    # First, upload the new image before deleting the old one

    # validate_image(thumbnail_image)
    await run_in_threadpool(validate_image, new_thumbnail_image)

    # webp_buffer = convert_to_webp(thumbnail_image)
    webp_buffer = await run_in_threadpool(convert_to_webp, new_thumbnail_image)

    existing_thumbnail_key: str | None = video.thumbnail_object_key
    new_thumbnail_key: str | None = None

    try:
        # thumbnail_key: str = upload_image_to_r2(webp_buffer, THUMBNAIL_BUCKET)
        new_thumbnail_key = await run_in_threadpool(
            upload_image_to_r2,
            webp_buffer,
            THUMBNAIL_BUCKET,
        )

        # Save a new VIDEO_EVENT
        video_event = VideoEvent(
            video_id=video_id,
            event_type = "THUMBNAIL_UPDATED",
            payload = {
                "content_type": "image/webp",
                "thumbnail_object_key": new_thumbnail_key,
                "filename": new_thumbnail_image.filename,
                "old_thumbnail_key": existing_thumbnail_key,
            },
        )
        session.add(video_event)

        # Assign the new thumbnail key to video
        video.thumbnail_object_key = new_thumbnail_key

        await session.commit()

        # Delete the older thumbnail
        if existing_thumbnail_key is not None:
            logger.info("Deleting existing thumbnail from R2: %s", existing_thumbnail_key)
            try:
                await run_in_threadpool(delete_image_from_r2, existing_thumbnail_key, THUMBNAIL_BUCKET)
            except ClientError:
                logger.exception("Failed to delete existing thumbnail from R2: %s", existing_thumbnail_key)

        return {
            "thumbnail_object_key": new_thumbnail_key,
        }

    except ClientError:
        # logger.exception() automatically includes the traceback
        logger.exception("Thumbnail upload failed for video %s", video_id)
        raise HTTPException(status_code=500, detail="S3 error.")

    except SQLAlchemyError:
        await session.rollback()

        # This avoids calling delete_object(Key=None) if the failure happened before the upload.
        if new_thumbnail_key is not None:
            logger.exception("Database commit failed. Deleting uploaded new thumbnail %s", new_thumbnail_key)

            try:
                await run_in_threadpool(delete_image_from_r2, new_thumbnail_key, THUMBNAIL_BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned new thumbnail from R2: %s", new_thumbnail_key)

        raise HTTPException(status_code=500, detail="Could not save thumbnail upload.")
