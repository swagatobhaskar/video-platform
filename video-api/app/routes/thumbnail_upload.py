import os
import shutil
import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from celery.result import AsyncResult
from sqlalchemy import select, Uuid
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
import kombu
import redis

from app.utils.r2_helper import s3
from app.utils.dependencies import get_db
from app.celery_worker import celery
from app.tasks.transcode.transcode_task import process_video_worker_operations

from app.database.models import (
    Video, UploadSession, UploadSessionStatusEnum, TranscodeTask, VideoProcessingStatusEnum,
    UploadPart, VideoEvent, VideoPublicationStatusEnum, VideoTranscript
)
from app.schemas.r2_upload_schema import ThumbnailUploadRequest
from app.database.session import AsyncSession

from app.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/video/thumbnail/", tags=["thumbnail",])

logger = logging.getLogger(__name__)

THUMBNAIL_BUCKET = settings.thumbnails_bucket

@router.post("/{video_id}/upload_url")
async def upload_thumbnail_for_video(
    video_id: str,
    req: ThumbnailUploadRequest,
    session: AsyncSession = Depends(get_db),
):
    try:
        import uuid
        thumbnail_key = f"{uuid.uuid4()}-{req.filename}"

        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": THUMBNAIL_BUCKET,
                "Key": thumbnail_key,
                "ContentType": req.contentType,
            },
            ExpiresIn=300,
        )

        return {
            "thumbnail_upload_url": url,
            "thumbnail_key": thumbnail_key,
        }

        # Save a VIDEO_EVENT
    except Exception as e:
        logger.warning(str(e))
        print(str(e))

@router.post("/{video_id}/upload-complete")
async def upload_thumbnail_for_video(
    video_id: str,
    # req: ThumbnailUploadRequest,
    session: AsyncSession = Depends(get_db),
):
    pass