import os
import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy import select
# from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from botocore.exceptions import ClientError

from app.utils.r2_helper import s3
from app.utils.image_helper import convert_to_webp, upload_image_to_r2
from app.utils.dependencies import get_db
from app.database.models import Video, VideoEvent
from app.schemas.r2_upload_schema import ThumbnailUploadComplete, ThumbnailUploadRequest
from app.database.session import AsyncSession

from app.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/thumbnail/", tags=["thumbnail",])

logger = logging.getLogger(__name__)

THUMBNAIL_BUCKET = settings.thumbnails_bucket

@router.post("video/{video_id}/upload")
async def upload_video_thumbnail(
    video_id: str,
    thumbnail_image: UploadFile = File(),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Video).where(Video.id == video_id)
    )

    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=400, detail=f"Video {video_id} not found!")

    # if uploaded image file is webp, bypass conversion

    try:
        

        # Save a new VIDEO_EVENT
        video_event = VideoEvent(
            video_id=video_id,
            event_type = "THUMBNAIL_PRESIGNED_UPLOAD_URL_GENERATED",
            payload = {
                "content_type": contentType,
                "expires_in": 300,
                "thumbnail_object_key": image_key,
                "filename": filename,
                # "upload_session": str(req.uploadSessionId),  # not required, I think
            },
        )
        session.add(video_event)
        await session.commit()

        return {
            "thumbnail_object_key": thumbnail_object_key,
        }

    except ClientError:
        logger.exception("...")
        raise HTTPException(status_code=500, detail="S3 error.")

    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Failed to save thumbnail upload event.")
        raise HTTPException(status_code=500, detail="Could not create upload session.")

