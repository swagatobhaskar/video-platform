import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
# from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from botocore.exceptions import ClientError

from app.utils.image_helper import convert_to_webp, upload_image_to_r2, validate_image, delete_image_from_r2
from app.utils.dependencies import get_db
from app.database.models import Video, VideoEvent
from app.database.session import AsyncSession

from app.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/thumbnail/", tags=["thumbnail",])

logger = logging.getLogger(__name__)

THUMBNAIL_BUCKET = settings.thumbnails_bucket

@router.post("/video/{video_id}/upload", status_code=201)
async def upload_video_thumbnail(
    video_id: str,
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

    except ClientError as e:
        # logger.exception() automatically includes the traceback
        logger.exception("Thumbnail upload failed")
        raise HTTPException(status_code=500, detail="S3 error.")

    except SQLAlchemyError as e:
        await session.rollback()

        # This avoids calling delete_object(Key=None) if the failure happened before the upload.
        if thumbnail_key is not None:
            logger.exception("Database commit failed. Deleting uploaded thumbnail %s", thumbnail_key)

            try:
                await run_in_threadpool(delete_image_from_r2, thumbnail_key, THUMBNAIL_BUCKET)
            except ClientError:
                logger.exception("Failed to delete orphaned thumbnail from R2: %s", thumbnail_key)

        raise HTTPException(status_code=500, detail="Could not save thumbnail upload.")
