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
    try:
        new_video = Video()
        db.add(new_video)

        new_upload_session = UploadSession(Video=new_video)
        db.add(new_upload_session)
        await db.commit()
        await db.refresh(new_video)
        await db.refresh(new_upload_session)  # if session uses expire_on_commit=False

        print("New Upload Session id: ", new_upload_session.id)
        print("New Video id: ", new_video.id)

        return {
            "success": True,
            "upload_session_id": str(new_upload_session.id),
            "video_id": str(new_video.id)
        }
    
    except SQLAlchemyError as e:
        print(e)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create new upload session and new video!"    
        )

@router.post('{video_id}/initiate-upload')
async def initiate_upload(
    video_id: str,
    req: InitiateUploadRequest,
    db: AsyncSession = Depends(get_db)
):

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

        # Get the video
        result = await db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(
                status_code=404,
                detail="No video found with this id."
            )

        video.title=req.fileName

        # db.add(video)
        await db.flush()

        # get the upload_session that was created when selecting the file
        stmt = select(UploadSession).where(
            UploadSession.id == req.uploadSessionId,
            UploadSession.video_id == video_id
        )

        result = await db.execute(stmt)
        upload_session = result.scalar_one_or_none()

        if not upload_session:
            raise HTTPException(status_code=404, detail="Upload session not found for the given uploadSessionId and video id")

        # upload_session.video_id=video.id
        upload_session.object_key=object_key
        upload_session.video_upload_id=upload_id
        upload_session.file_size_bytes=req.fileSizeBytes
        upload_session.mime_type=req.contentType
        upload_session.original_filename=req.fileName
        upload_session.total_parts=req.totalParts
        upload_session.status=UploadSessionStatusEnum.UPLOADING

        video_event = VideoEvent(
            video_id=video_id,
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

        db.add(video_event)
        await db.commit()
        await db.refresh(upload_session)

        return {
            "uploadId": upload_id,
            "key": object_key,
            "upload_session_id": str(upload_session.id),
            "video_id": video.id,
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


@router.post("{video_id}/get-presigned-url")
async def get_presigned_url(
    video_id: str,
    req: PartRequest,
    db: AsyncSession = Depends(get_db)    
):
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
    try:
        video_event = VideoEvent(
            video_id = video_id,
            event_type=f"PART {req.partNumber} UPLOADED",
            payload={
                "upload_id": req.uploadId,
                "object_key": req.key,
                "part_number": req.partNumber
            }
        )

        db.add(video_event)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.exception("VideoEvent creation failed at /get-presigned-url.")
    
    # print("Generated presigned URL: ", url)
    return {"uploadUrl": url}


def get_uploaded_parts(s3, bucket: str, key: str, uploadId: str):
    response = s3.list_parts(
        Bucket=bucket,
        Key=key,
        UploadId=uploadId
    )
    
    return response.get("Parts", [])


@router.post("/{video_id}/complete-upload")
async def complete_upload(video_id: str, req: CompleteRequest, db: AsyncSession = Depends(get_db)):
    
    # Later Additions:
        # Ordering check
        # ETag validation
        # Storage verification
    
    # phase 1: complete upload
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

        result = await db.execute(
            select(UploadSession).where(
                UploadSession.id == req.uploadSessionId,
                UploadSession.video_id == video_id
            )
        )
        upload_session = result.scalars().first() # scalar_one_or_none()
        
        if not upload_session:
            raise HTTPException(status_code=404, detail="Upload session not found for the given video ID")
        
        # Create a new VideoEvent instead of updating old events
        video_event = VideoEvent(
            video_id=video_id,
            event_type="CHUNKS_UPLOAD_COMPLETED",
            payload={
                "upload_id": req.uploadId,
                "object_key": req.key,
                "file_name": req.key,  # Assuming the key is the filename
            }
        )

        db.add(video_event)

        upload_session.status = UploadSessionStatusEnum.COMPLETED
        upload_session.uploaded_parts_count = len(uploaded_parts) # upload_session.total_parts

        await db.commit()

    except Exception as e:
        await db.rollback()
        logger.exception("Complete upload failed")
        
        result = await db.execute(
            select(UploadSession).where(
                UploadSession.id == req.uploadSessionId,
                UploadSession.video_id == video_id    
            )
        )
        upload_session = result.scalars().first()
    
        if upload_session:
            upload_session.status = UploadSessionStatusEnum.FAILED
            await db.commit()

        raise HTTPException(status_code=500, detail=str(e))
    
    # Phase 2: Create a TranscodeTask
    try:        
        logger.info("Adding transcode task for %s", req.key)

        # Create A TranscodeTask entry
        transcode_task = TranscodeTask(
            video_id=req.videoId,
            upload_session_id=req.uploadSessionId,
            status=VideoProcessingStatusEnum.PENDING,
        )

        db.add(transcode_task)
        await db.flush()   # Get transcode_task_id # INSERT happens, UUID becomes available
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Failed creating TranscodeTask")
        raise  # I think it should raise HTTPException saying something!

    # Phase 3: Send Task to Redis
    task_id: str | None = None
    try:
        # start celery transcode task
        task = process_video_worker_operations.delay( # type: ignore
            file_name=req.key,
            video_id=req.videoId,  # or video_id ?
            upload_id=req.uploadId,
            upload_session_id=req.uploadSessionId,
            transcode_task_id=str(transcode_task.id),
        )
        
        task_id = str(task.id)
        # print("TASK ID: ", task.id)
        transcode_task.status = VideoProcessingStatusEnum.QUEUED
        await db.commit()

        logger.info("Task queued: %s", task.id)
    
    except (
        redis.exceptions.ConnectionError,
        kombu.exceptions.OperationalError,
        RuntimeError
    ) as e:
        # print(f"Redis task sending error: {e}")
        transcode_task.status = VideoProcessingStatusEnum.QUEUE_FAILED
        await db.commit()

        logger.exception("Couldn't queue task")
        logger.exception("Exception type: %s", type(e))

        # Don't raise 500, because upload is already completed. Just inform the user that processing is unavailable.
        # raise HTTPException(
        #     status_code=503,
        #     detail="Upload completed but processing is unavailable."
        # )
        
    return {
        "success": True,
        "taskId": task_id if task_id else "Transcoding QUEUE_FAILED",
        "status": "upload completed",
        "message": (
            "Upload completed and processing task queued." if task_id 
            else "Upload completed. Processing is PENDING. \
                Task will be queued when the service is available."
        ),
    }


@router.post("/{video_id}/abort-upload")
async def abort_upload(video_id: str, req: AbortRequest, db:AsyncSession = Depends(get_db)):
    try:
        s3.abort_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
        )

        # get video_id from upload_id
        result = await db.execute(
            select(UploadSession).where(
                UploadSession.video_upload_id == req.uploadId,
                UploadSession.video_id == video_id    
            )
        )
        upload_session = result.scalar_one_or_none()

        if not upload_session:
            raise ValueError("Upload session not found for the given upload ID")

        # Add a VideoEvent to the DB
        video_event = VideoEvent(
            event_type = "CHUNKS_UPLOAD_ABORTED",
            video_id=video_id,
            # video_id = req.videoId,
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


@router.post("/{video_id}/{upload_id}/pause-upload")
async def pause_video_upload(video_id: str, upload_id: str, db:AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(UploadSession).where(
            UploadSession.upload_id == upload_id,
            UploadSession.video_id == video_id
        )
    )

    upload_session = result.scalar_one_or_none()

    if not upload_session:
        raise HTTPException(status=404, detail="Upload session not found")
    
    if upload_session.status != UploadSessionStatusEnum.UPLOADING:
        raise HTTPException(status=400, detail="Upload session is not in UPLOADING state")
    
    upload_session.status = UploadSessionStatusEnum.PAUSED

    # Add a VideoEvent to the DB
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_PAUSED",
        video_id=video_id,
        payload = {
            "upload_id": upload_id,
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
        },
    )
    db.add(video_event)
        
    await db.commit()

    return { "success": True, "status": "paused"}


@router.post("/{video_id}/{upload_id}/resume-upload")
async def resume_video_upload(video_id: str, upload_id: str, db:AsyncSession = Depends(get_db)):
    
    result = await db.execute(
        select(UploadSession).where(
            UploadSession.upload_id == upload_id,
            UploadSession.video_id == video_id
        )
    )

    upload_session = result.scalar_one_or_none()

    if not upload_session:
        raise HTTPException(status=404, detail="Upload session not found")
    
    if upload_session.status != UploadSessionStatusEnum.PAUSED:
        raise HTTPException(status=400, detail="Upload session is not in PAUSED state")
    
    upload_session.status = UploadSessionStatusEnum.UPLOADING

    # Frontend asks which parts already exist.
    # result = await db.execute(
    #     select(UploadPart).where(UploadPart.upload_session_id == upload_session.id)
    # )
    # uploaded_parts = result.scalars().all()

    # Ask R2 which parts actually exist
    uploaded_parts = get_uploaded_parts(
        s3=s3,
        bucket=RAW_VIDEO_BUCKET,
        key=upload_session.object_key,
        uploadId=upload_session.video_upload_id,
    )

    # Add a VideoEvent to the DB
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_RESUMED",
        video_id = video_id,
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
        select(UploadSession).where(
            UploadSession.video_upload_id == upload_id,
            UploadSession.video_id == video_id
        )
    )

    upload_session = result.scalar_one_or_none()

    if not upload_session:
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

# transcode_task_id could be optional
# So changing it iinto route query parameter
@router.get("/{video_id}/processing-status/{transcode_task_id}")
async def get_transcode_processing_status(
    video_id: str,
    transcode_task_id: str,
    db: AsyncSession = Depends(get_db)
):    
    result = await db.execute(
        select(Video).where(Video.id == video_id)
    )

    video = await result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=404,
            detail=f"Video with id {video_id} not found!"
        )
    
    if video.transcode_task_id != transcode_task_id:
        raise HTTPException(
            status_code=503,
            detail="Task id doesn't belong to the video"
        )
    
    # transcode_task_result = await db.execute(
    #     select(TranscodeTask).where(TranscodeTask.id == transcode_task_id)
    # )

    # transcode_task = transcode_task_result.scalar_one_or_none()

    # If transcode_task_id is not present
    # if not transcode_task:
    #     raise HTTPException(
    #         status_code=404,
    #         detail=f"Video with id {video_id} not found!"
    #     )

    status = AsyncResult(transcode_task_id, app=celery)

    return {
        "task_id": transcode_task_id,
        "status": status.status,
        "result": status.result
    }


@router.post("/{video_id}/retry-upload")
async def retry_failed_upload(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Find the latest failed/paused upload session
    result = await db.execute(
        select(UploadSession).where(
            # UploadSession.video_upload_id == upload_id,
            UploadSession.video_id == video_id,
            UploadSession.status.in_([
                UploadSessionStatusEnum.FAILED,
                UploadSessionStatusEnum.PAUSED,
            ])
        )
        .order_by(UploadSession.created_at.desc())
    )

    upload_session = result.scalars().first()

    if upload_session is None:
        raise HTTPException(status=404, detail="No failed upload session found.")

    # Ask R2 which parts actually exist
    uploaded_parts = get_uploaded_parts(
        s3=s3,
        bucket=RAW_VIDEO_BUCKET,
        key=upload_session.object_key,
        uploadId=upload_session.video_upload_id,
    )

    upload_session.status = UploadSessionStatusEnum.UPLOADING

    # get the chunks already uploaded
    # stmt = select(UploadPart).where(UploadPart.upload_session_id == upload_session.id)
    # result = await db.execute(stmt)
    # uploaded_parts = result.scalars().all()

    # Add a VideoEvent to the DB
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_RETRY",
        video_id=video_id,
        payload = {
            "upload_id": str(upload_session.video_upload_id),
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
            "upload_session": str(upload_session.id),
            "uploaded_parts": len(uploaded_parts)
        },
    )
    db.add(video_event)
        
    await db.commit()

    # Frontend Retry button
    # ↓
    # POST /retry-upload
    # ↓
    # receive

    # uploadId
    # objectKey
    # uploadedParts
    # ↓
    # Skip uploaded parts
    # ↓
    # Upload only missing parts
    # ↓
    # CompleteMultipartUpload

    return {
        "video_id": video_id,
        "upload_session_id": str(upload_session.id),
        "upload_id": upload_session.video_upload_id,
        "object_key": upload_session.object_key,
        "uploaded_parts": uploaded_parts,
    }


@router.post("/{video_id}/restart-upload")
async def restart_video_upload(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UploadSession)
        .where(
            UploadSession.video_id == video_id
        )
        .order_by(UploadSession.created_at.desc())
    )

    old_session = result.scalars().first()

    if old_session is None:
        raise HTTPException(
            status_code=404,
            detail="Upload session not found."
        )

    new_session = UploadSession(
        video_id=old_session.video_id,
        file_size_bytes=old_session.file_size_bytes,
        mime_type=old_session.mime_type,
        original_filename=old_session.original_filename,
        total_parts=old_session.total_parts,
        status=UploadSessionStatusEnum.PENDING,
    )

    db.add(new_session)
    await db.flush()

    db.add(
        VideoEvent(
            video_id=video_id,
            event_type="UPLOAD_RESTARTED",
            payload={
                "old_upload_session_id": str(old_session.id),
                "new_upload_session_id": str(new_session.id),
            },
        )
    )

    await db.commit()

    # there is no uploaded_parts. The old chunks belong to another multipart upload.

    return {
        "video_id": video_id,
        "upload_session_id": str(new_session.id),
    }
    # Frontend
    # Restart button
    # ↓
    # POST /restart-upload
    # ↓
    # receive

    # new upload_session_id
    # ↓
    # POST /initiate-upload
    # ↓
    # receive

    # new uploadId
    # new objectKey
    # ↓
    # Upload ALL chunks
    # ↓
    # Complete upload
    