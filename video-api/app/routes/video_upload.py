import os
import shutil
import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from celery.result import AsyncResult
from sqlalchemy.ext import AsyncSession
from sqlalchemy import select, Uuid
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi.responses import JSONResponse

from app.utils.r2_helper import s3
from app.utils.dependencies import get_db
from app.celery_worker import celery
from app.tasks.transcode.transcode_task import process_video_worker_operations

from app.database.models import Video, UploadSession, UploadSessionStatusEnum
from app.schemas.r2_upload_schema import CompleteRequest, PartRequest, InitiateUploadRequest, AbortRequest
from app.database.session import AsyncSession

router = APIRouter(prefix="/api/video/uploads", tags=["video", "upload"])

logger = logging.getLogger(__name__)

# @router.post('/video')
# async def upload_video(file: UploadFile = File(...), title: str = Form(...)):
#     # Basic validation: ensure it's an image
#     if not file.content_type.startswith("video/"):
#         raise HTTPException(status_code=400, detail="File must be a video!")
    
#     # Create a local path to save the video
#     video_file_location = f"videos/{file.filename}"
#     os.makedirs("videos", exist_ok=True)
    
#     with open(video_file_location, "wb+") as file_object:
#         # Stream the file content to disk
#         shutil.copyfileobj(file.file, file_object)
    
#     return {"info": f"Video '{title}' saved at {video_file_location}"}


# @router.post('/thumbnail')
# async def upload_thumbnail(file: UploadFile = File(...)):
#     # Basic validation: ensure it's an image
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="File must be an image!")
    
#     # Create a local path to save the video
#     thumbnail_file_location = f"thumbnails/{file.filename}"
#     os.makedirs("thumbnails", exist_ok=True)
    
#     with open(thumbnail_file_location, "wb+") as file_object:
#         # Stream the file content to disk
#         shutil.copyfileobj(file.file, file_object)
    
#     return {"info": f"Video thumbnail {file.filename} saved at {thumbnail_file_location}"}


RAW_VIDEO_BUCKET: str = 'raw-video-upload-bucket'

@router.post('/initiate-upload')
async def initiate_upload(req: InitiateUploadRequest, db: AsyncSession = Depends(get_db)):
    
    # Use {UUID}-{filename} instead of just filename
    import uuid
    unique_filename_key = f"{uuid.uuid4()}" #-{req.fileName}"
    
    response = s3.create_multipart_upload(
        Bucket=RAW_VIDEO_BUCKET,
        Key=unique_filename_key, # req.fileName,
        ContentType=req.contentType
    )
    # print("Initiate Upload Response: ", response)

    video = Video(video_object_storage_prefix="")

    db.add(video)
    await db.flush()
    
    upload_session = UploadSession(
        video_id=video.id,
        object_key=response['Key'],
        video_upload_id=response["UploadId"],
        file_size_bytes=req.fileSizeBytes,
        mime_type=req.contentType,
        original_filename=req.fileName,
        total_parts=req.totalParts,
        status=UploadSessionStatusEnum.UPLOADING,
    )

    db.add(upload_session)
    await db.commit()

    return {
        "uploadId": response["UploadId"],
        "key": response["Key"],
    }

@router.post("/{upload_id}/get-presigned-url")
def get_presigned_url(req: PartRequest):
    url = s3.generate_presigned_url(
        ClientMethod="upload_part",
        Params={
            "Bucket": RAW_VIDEO_BUCKET,
            "Key": req.key,
            "UploadId": req.uploadId,
            "PartNumber": req.partNumber,
        },
        ExpiresIn=3600,
    )
    print("Generated presigned URL: ", url)
    return {"uploadUrl": url}


def get_uploaded_parts(s3, bucket: str, key: str, uploadId: str):
    response = s3.list_parts(
        Bucket=bucket,
        Key=key,
        UploadId=uploadId
    )
    
    return response.get("Parts", [])

@router.post("/{upload_id}/complete-upload")
def complete_upload(req: CompleteRequest):
    
    # Later Additions:
        # Ordering check
        # ETag validation
        # Storage verification
        
    try:
        # Verify actual uploaded parts with R2
        uploaded_parts = get_uploaded_parts(
            s3,
            RAW_VIDEO_BUCKET,
            req.key,
            req.uploadId
        )
        
        if len(uploaded_parts) != len(req.parts):
            raise ValueError("Mismatch between uploaded parts and client parts")
        
        # Complete upload
        s3.complete_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
            MultipartUpload={
                # "Parts": req.parts,  # [{ETag, PartNumber}]
                "Parts": [
                    {
                        "ETag": part.ETag,
                        "PartNumber": part.PartNumber
                    }
                    for part in req.parts
                ]
            },
        )
        
        # print(f"File name/key: {req.key}")
        
        logger.info("Sending transcode task for %s", req.key)
        # start a celery task
        task = process_video_worker_operations.delay( # type: ignore
            file_name=req.key
        )
        logger.info("Task queued: %s", task.id)
        
        return {
            "success": True,
            "taskId": task.id,
            "status": "upload completed",
        }
    
    except Exception as e:
        return {"error": str(e)}

@router.post("/{upload_id}/abort-upload")
def abort_upload(req: AbortRequest):
    try:
        s3.abort_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
        )
        return {"success": True, "status": "aborted"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/{upload_id}/processing-status/{transcode_task_id}")
def get_transcode_processing_status(transcode_task_id: str):
    status = AsyncResult(transcode_task_id, app=celery)
        
    return {
        "task_id": transcode_task_id,
        "status": status.status,
        "result": status.result
    }

@router.post("/{upload_id}/pause-upload")
async def pause_video_upload(upload_id: str, db:AsyncSession = Depends(get_db)):
    pass