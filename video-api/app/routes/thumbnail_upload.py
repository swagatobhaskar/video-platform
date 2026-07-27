import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError

from app.utils.r2_helper import s3
from app.utils.dependencies import get_db
from app.tasks.transcode.transcode_task import process_video_worker_operations

from app.database.models import (
    Video, UploadSession, UploadSessionStatusEnum, VideoProcessingStatusEnum,
    VideoEvent,
)
from app.schemas.r2_upload_schema import ThumbnailUploadComplete, ThumbnailUploadRequest
from app.database.session import AsyncSession

from app.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/video/thumbnail/", tags=["thumbnail",])

logger = logging.getLogger(__name__)

THUMBNAIL_BUCKET = settings.thumbnails_bucket

@router.post("/{video_id}/upload_url")
async def upload_video_thumbnail(
    video_id: str,
    req: ThumbnailUploadRequest,
    session: AsyncSession = Depends(get_db),
):
    ALLOWED_THUMBNAIL_TYPES = {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    }

    MAX_SIZE = 5 * 1024 * 1024  # 5 MB

    if req.contentType not in ALLOWED_THUMBNAIL_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    if req.fileSizeBytes > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Thumbnail too large")

    try:
        import uuid
        thumbnail_object_key = uuid.uuid4()  # This avoids weird filenames like ../../cat.png

        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": THUMBNAIL_BUCKET,
                "Key": thumbnail_object_key,
                "ContentType": req.contentType,
            },
            ExpiresIn=300,
        )

        # Save a new VIDEO_EVENT
        video_event = VideoEvent(
            video_id=video_id,
            event_type = "THUMBNAIL_PRESIGNED_UPLOAD_URL_GENERATED",
            payload = {
                "content_type": req.contentType,
                "expires_in": 300,
                "thumbnail_object_key": thumbnail_object_key,
                "filename": req.filename,
                # "upload_session": str(req.uploadSessionId),  # not required, I think
            },
        )
        session.add(video_event)
        await session.commit()

        return {
            "thumbnail_upload_url": url,
            "thumbnail_object_key": thumbnail_object_key,
        }

    except Exception as e:
        logger.exception(str(e))
        print(str(e))


@router.post("/{video_id}/upload-complete")
async def thumbnail_upload_complete(
    video_id: str,
    req: ThumbnailUploadComplete,
    session: AsyncSession = Depends(get_db),
):
    try:
        s3.head_object(
            Bucket=THUMBNAIL_BUCKET,
            Key=req.thumbnail_object_key,
        )
    except ClientError:
        raise HTTPException(status_code=400, detail="Thumbnail not found in storage.")
    
    try:
        result = await session.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

        video.thumbnail_object_key = req.thumbnail_object_key

        # Save a new VIDEO_EVENT
        video_event = VideoEvent(
            video_id=video_id,
            event_type = "THUMBNAIL_OBJECT_KEY_ASSIGNED_TO_VIDEO",
            payload = {
                "thumbnail_object_key": req.thumbnail_object_key,
                "file_name": req.filename,
                # "upload_session": str(req.uploadSessionId),
            },
        )
        session.add(video_event)
        await session.commit()

    except SQLAlchemyError as e:
        logger.exception(f"Encountered SQLAlchemy error when assigning thumbnail_object_key to Video. {e}")
        await session.rollback()

    return {
        "status": "success",
        "thumbnail_object_key": req.thumbnail_object_key
    }
