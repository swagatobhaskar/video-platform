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

from app.utils.r2_helper import s3
from app.utils.dependencies import get_db
from app.celery_worker import celery
from app.tasks.transcode.transcode_task import process_video_worker_operations

from app.database.models import (
    Video, UploadSession, UploadSessionStatusEnum,
    UploadPart, VideoEvent, VideoPublicationStatusEnum, VideoTranscript
)
from app.schemas.r2_upload_schema import CompleteRequest, Part, PartRequest, InitiateUploadRequest, AbortRequest
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


@router.post("/new-upload-session")
async def create_new_upload_session(db: AsyncSession = Depends(get_db)):
    new_upload_session = UploadSession()


@router.post('/initiate-upload')
async def initiate_upload(req: InitiateUploadRequest, db: AsyncSession = Depends(get_db)):

    upload_id = None
    object_key = None

    try:
        # Use {UUID}-{filename} instead of just filename
        import uuid
        object_key = f"{uuid.uuid4()}" #-{req.fileName}"
        
        response = s3.create_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=object_key,
            ContentType=req.contentType
        )
        # print("Initiate Upload Response: ", response)
        upload_id = response["UploadId"]

        video = Video(title=req.fileName)

        db.add(video)
        await db.flush()

        upload_session = UploadSession(
            video_id=video.id,
            object_key=object_key,
            video_upload_id=upload_id,
            file_size_bytes=req.fileSizeBytes,
            mime_type=req.contentType,
            original_filename=req.fileName,
            total_parts=req.totalParts,
            status=UploadSessionStatusEnum.UPLOADING,
        )

        video_event = VideoEvent(
            video_id=video.id,
            event_type="UPLOAD_INITIATED",
            payload={
                "upload_id": upload_id,
                "object_key": object_key,
                "file_name": req.fileName,
                "file_size_bytes": req.fileSizeBytes,
                "content_type": req.contentType,
                "total_parts": req.totalParts
            }
        )

        db.add_all([upload_session, video_event])
        await db.commit()
        await db.refresh(upload_session)

        return {
            "uploadId": upload_id,
            "key": object_key,
            "upload_session_id": str(upload_session.id),
        }

    except Exception as e:
        await db.rollback()    
    
        # Clean up R2 multipart upload if it was created
        if upload_id and object_key:
            try:
                s3.abort_multipart_upload(
                    Bucket=RAW_VIDEO_BUCKET,
                    Key=object_key,
                    UploadId=upload_id
                )
            except Exception:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate upload: {str(e)}"
        )


@router.post("/get-presigned-url")
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
    # print("Generated presigned URL: ", url)
    return {"uploadUrl": url}


def get_uploaded_parts(s3, bucket: str, key: str, uploadId: str):
    response = s3.list_parts(
        Bucket=bucket,
        Key=key,
        UploadId=uploadId
    )
    
    return response.get("Parts", [])


@router.post("/complete-upload")
async def complete_upload(
    req: CompleteRequest,
    # upload_id: str,
    db: AsyncSession = Depends(get_db)
):
    
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

        # Create a new VideoEvent instead of updating old events
        video_event = VideoEvent(
            video_id=req.videoId,
            event_type="CHUNKS_UPLOAD_COMPLETED",
            payload={
                "upload_id": req.uploadId,
                "object_key": req.key,
                "file_name": req.key,  # Assuming the key is the filename
            }
        )

        db.add(video_event)

        # Also update UploadSession status to COMPLETED
        result = await db.execute(
            select(UploadSession).where(UploadSession.video_upload_id == req.uploadId) # That's guaranteed unique. A video could theoretically have multiple upload sessions.
        )
        upload_session = result.scalar_one_or_none()

        if not upload_session:
            raise ValueError("Upload session not found for the given video ID")
        
        upload_session.status = UploadSessionStatusEnum.COMPLETED
        upload_session.uploaded_parts_count = len(uploaded_parts) # upload_session.total_parts

        await db.commit()

        # print(f"File name/key: {req.key}")
        
        logger.info("Sending transcode task for %s", req.key)
        # start celery transcode task
        task = process_video_worker_operations.delay( # type: ignore
            file_name=req.key,
            video_id=req.videoId,
            upload_id=req.uploadId, #upload_id, # from function argument
            upload_session_id=req.uploadSessionId,
        )

        logger.info("Task queued: %s", task.id)
        
        return {
            "success": True,
            "taskId": task.id,
            "status": "upload completed",
        }
    
    except Exception as e:
        await db.rollback()

        result = await db.execute(
            select(UploadSession).where(UploadSession.video_id == req.videoId)
        )
        upload_session = result.scalar_one_or_none()
    
        if upload_session:
            upload_session.status = UploadSessionStatusEnum.FAILED
            await db.commit()

        return {"error": str(e)}


@router.post("/{upload_id}/abort-upload")
async def abort_upload(req: AbortRequest, upload_id: str, db:AsyncSession = Depends(get_db)):
    try:
        s3.abort_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
        )

        # get video_id from upload_id
        result = await db.execute(
            select(UploadSession).where(UploadSession.video_upload_id == upload_id)
        )
        upload_session = result.scalar_one_or_none()

        if not upload_session:
            raise ValueError("Upload session not found for the given upload ID")

        # Add a VideoEvent to the DB
        video_event = VideoEvent(
            event_type = "CHUNKS_UPLOAD_ABORTED",
            video_id=upload_session.video_id,
            payload = {
                "upload_id": req.uploadId,
                "object_key": req.key,
                "file_name": req.key,  # Assuming the key is the filename
            },
        )
        db.add(video_event)

        upload_session.status = UploadSessionStatusEnum.ABORTED

        await db.commit()

        return {"success": True, "status": "aborted"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/{upload_id}/pause-upload")
async def pause_video_upload(upload_id: str, db:AsyncSession = Depends(get_db)):
    upload_session = await db.get(UploadSession, upload_id)

    if not upload_session:
        raise HTTPException(status=404, detail="Upload session not found")
    
    if upload_session.status != UploadSessionStatusEnum.UPLOADING:
        raise HTTPException(status=400, detail="Upload session is not in UPLOADING state")
    
    upload_session.status = UploadSessionStatusEnum.PAUSED

    # Add a VideoEvent to the DB
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_PAUSED",
        video_id=upload_session.video_id,
        payload = {
            "upload_id": upload_id,
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
        },
    )
    db.add(video_event)
        
    await db.commit()

    return { "success": True, "status": "paused"}


@router.post("/{upload_id}/resume-upload")
async def resume_video_upload(upload_id: str, db:AsyncSession = Depends(get_db)):
    upload_session = await db.get(UploadSession, upload_id)

    if not upload_session:
        raise HTTPException(status=404, detail="Upload session not found")
    
    if upload_session.status != UploadSessionStatusEnum.PAUSED:
        raise HTTPException(status=400, detail="Upload session is not in PAUSED state")
    
    upload_session.status = UploadSessionStatusEnum.UPLOADING

    # Frontend asks which parts already exist.
    result = await db.execute(
        select(UploadPart).where(UploadPart.upload_session_id == upload_session.id)
    )
    uploaded_parts = result.scalars().all()

    # Add a VideoEvent to the DB
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_RESUMED",
        video_id=upload_session.video_id,
        payload = {
            "upload_id": upload_id,
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
        },
    )
    
    db.add(video_event)

    await db.commit()

    return {
        "success": True,
        "status": "resumed",
        "upload_id": upload_id,
        "uploaded_parts": uploaded_parts,
    }


# Record Uploaded Part
# After a successful chunk upload, frontend sends ETag.
@router.post("/{upload_id}/{video_id}/record-uploaded-part")
async def record_uploaded_part(
    upload_id: str,
    video_id: str,
    part: Part,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(UploadSession).where(UploadSession.video_upload_id == upload_id)
    )
    upload_session = result.scalar_one_or_none()

    if upload_session is None:
        raise HTTPException(
            status_code=404,
            detail="Upload session not found."
        )

    try:
        new_part = UploadPart(
            upload_session_id=upload_session.id,
            part_number=part.PartNumber,
            etag=part.ETag,
            size_bytes=part.SizeBytes,
        )
        db.add(new_part)
        
        # Increment uploaded parts count by 1
        upload_session.uploaded_parts_count += 1

        # Add a VideoEvent to the DB
        video_event = VideoEvent(
            event_type = "CHUNK_UPLOADED",
            video_id=video_id,
            payload = {
                "upload_session_id": str(upload_session.id),
                "upload_id": upload_id,
                "partNumber": part.PartNumber,
                "ETag": part.ETag,
                "size_bytes": part.SizeBytes,
            }
        )
        db.add(video_event)

        await db.commit()

    except IntegrityError:
        # catch it. Then simply return success. Duplicate chunk uploads are perfectly normal.
        # raise HTTPException(status=400, detail="This part has already been recorded.")
        await db.rollback() 
        return {
            "success": True,
            "message": "uploaded part already recorded"
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status=500, detail=str(e))

    return {
        "success": True,
        "message": "uploaded part recorded successfully"
    }


@router.get("/{upload_id}/processing-status/{transcode_task_id}")
def get_transcode_processing_status(transcode_task_id: str):
    status = AsyncResult(transcode_task_id, app=celery)
        
    return {
        "task_id": transcode_task_id,
        "status": status.status,
        "result": status.result
    }


@router.post("/{upload_id}/retry-upload")
async def retry_failed_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db)
):
    upload_session = await db.get(UploadSession, upload_id)

    if not upload_session:
        raise HTTPException(status=404, detail="Upload session not found")
    
    if upload_session.status != UploadSessionStatusEnum.FAILED:
        raise HTTPException(status=400, detail="Upload session is not in FAILED state")
    
    # get the chunks already uploaded
    stmt = select(UploadPart).where(UploadPart.upload_session_id == upload_session.id)
    result = await db.execute(stmt)
    uploaded_parts = result.scalars().all()

    # Add a VideoEvent to the DB
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_RETRY",
        video_id=upload_session.video_id,
        payload = {
            "upload_id": upload_id,
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
        },
    )
    db.add(video_event)

    upload_session.status = UploadSessionStatusEnum.UPLOADING
        
    await db.commit()

    return {
        "status": "retrying",
        "upload_id": upload_id,
        "uploaded_parts": uploaded_parts,
    }

