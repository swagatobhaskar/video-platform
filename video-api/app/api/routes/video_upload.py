# import os
# import shutil
import logging
from fastapi import APIRouter, HTTPException, Depends # , File, UploadFile, Form
from celery.result import AsyncResult
from sqlalchemy import select

from app.dependencies import get_upload_service, get_video_repository, get_transcode_repository
from app.workers.celery_worker import celery
from app.schemas.r2_upload_schema import CompleteRequest, Part, PartRequest, InitiateUploadRequest, AbortRequest
from app.exceptions.video import VideoNotFound
from app.exceptions.transcodetask import TranscodeTaskMismatch, TranscodeTaskNotFound
from app.repositories.video_repository import VideoRepository
from app.repositories.transcode_repository import TranscodeRepository
from app.services.upload_service import UploadService
# from app.services.storage.r2_storage_service import R2StorageService

from app.core.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/video/upload", tags=["video", "upload"])

logger = logging.getLogger(__name__)


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

# Route doesn't need to know about bucket
# RAW_VIDEO_BUCKET = settings.raw_videos_bucket

@router.post("/new-upload-record")
async def create_new_upload_record(upload_service: UploadService = Depends(get_upload_service)):
    return await upload_service.new_upload_record()


@router.post('/{video_id}/initiate-upload')
async def initiate_upload(
    video_id: str,
    req: InitiateUploadRequest,
    # session: AsyncSession = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.initiate(
        contentType=req.contentType,
        fileName=req.fileName,
        upload_session_id=req.uploadSessionId,
        video_id=video_id,
        fileSizeBytes=req.fileSizeBytes,
        totalParts=req.totalParts,
    )
    # upload_id = None
    # object_key = None

    # try:
        # Use {UUID}-{filename} instead of just filename
        # import uuid
        # object_key = f"{uuid.uuid4()}" #-{req.fileName}"
       
        # response = s3.create_multipart_upload(
        #     Bucket=RAW_VIDEO_BUCKET,
        #     Key=object_key,
        #     ContentType=req.contentType
        # )
        # print("Initiate Upload Response: ", response)
        # upload_id = response["UploadId"]

        # Get the video
        # result = await session.execute(
        #     select(Video).where(Video.id == video_id)
        # )
        # video = result.scalar_one_or_none()

        # if not video:
        #     raise HTTPException(
        #         status_code=404,
        #         detail="No video found with this id."
        #     )

        # video.title=req.fileName

        # # session.add(video)
        # await session.flush()

        # get the upload_session that was created when selecting the file
        # stmt = select(UploadSession).where(
        #     UploadSession.id == req.uploadSessionId,
        #     UploadSession.video_id == video_id
        # )

        # result = await session.execute(stmt)
        # upload_session = result.scalar_one_or_none()

        # if not upload_session:
        #     raise HTTPException(status_code=404, detail="Upload session not found for the given uploadSessionId and video id")

        # upload_session.object_key=object_key
        # upload_session.video_upload_id=upload_id
        # upload_session.file_size_bytes=req.fileSizeBytes
        # upload_session.mime_type=req.contentType
        # upload_session.original_filename=req.fileName
        # upload_session.total_parts=req.totalParts
        # upload_session.status=UploadSessionStatusEnum.UPLOADING

        # video_event = VideoEvent(
        #     video_id=video_id,
        #     event_type="UPLOAD_INITIATED",
        #     payload = {
        #         "upload_id": upload_id,
        #         "object_key": object_key,
        #         "file_name": req.fileName,
        #         "file_size_bytes": req.fileSizeBytes,
        #         "content_type": req.contentType,
        #         "total_parts": req.totalParts,
        #         "upload_session_id": str(req.uploadSessionId),
        #     }
        # )

        # session.add(video_event)
        # await session.commit()
        # await session.refresh(upload_session)

        # return {
        #     "uploadId": upload_id,
        #     "key": object_key,
        # }

    # except Exception as e:
    #     await session.rollback()    
    
    #     # Clean up R2 multipart upload if it was created
    #     if upload_id and object_key:
    #         try:
    #             s3.abort_multipart_upload(
    #                 Bucket=RAW_VIDEO_BUCKET,
    #                 Key=object_key,
    #                 UploadId=upload_id
    #             )
    #         except Exception:
    #             pass
        
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Failed to initiate upload: {str(e)}"
    #     )


@router.post("/{video_id}/get-presigned-url")
async def get_presigned_url(
    video_id: str,
    req: PartRequest,
    # session: AsyncSession = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.get_presigned_url(
        video_id=video_id,
        upload_id=req.uploadId,
        object_key=req.key,
        part_number=req.partNumber
    )

    # url = s3.generate_presigned_url(
    #     ClientMethod="upload_part",
    #     Params={
    #         "Bucket": RAW_VIDEO_BUCKET,
    #         "Key": req.key,
    #         "UploadId": req.uploadId,
    #         "PartNumber": req.partNumber,
    #     },
    #     ExpiresIn=3600,
    # )
    
    # try:
        # video_event = VideoEvent(
        #     video_id = video_id,
        #     event_type="GENERATED_PRESIGNED_URL",
        #     payload={
        #         "upload_id": req.uploadId,
        #         "object_key": req.key,
        #         "part_number": req.partNumber
        #     }
        # )

    #     session.add(video_event)
    #     await session.commit()
    # except SQLAlchemyError as e:
    #     await session.rollback()
    #     logger.exception("VideoEvent creation failed at /get-presigned-url.")
    
    # print("Generated presigned URL: ", url)
    # return {"uploadUrl": url}


def get_uploaded_parts(s3, bucket: str, key: str, uploadId: str):
    response = s3.list_parts(
        Bucket=bucket,
        Key=key,
        UploadId=uploadId
    )
    
    return response.get("Parts", [])


@router.post("/{video_id}/complete-upload")
async def complete_upload(
    video_id: str,
    req: CompleteRequest,
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.complete(
        video_id=video_id,
        upload_session_id=req.uploadSessionId,
        upload_id=req.uploadId,
        object_key=req.key
    )
    """
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

        result = await session.execute(
            select(UploadSession).where(
                UploadSession.id == req.uploadSessionId,
                UploadSession.video_id == video_id
            )
        )
        upload_session = result.scalar_one_or_none()  # scalars().first()
        
        if not upload_session:
            raise HTTPException(status_code=404, detail="Upload session not found for the given video ID")
        
        # Create a new VideoEvent instead of updating old events
        video_event = VideoEvent(
            video_id=video_id,
            event_type="CHUNKS_UPLOAD_COMPLETED",
            payload={
                "upload_id": req.uploadId,
                "object_key": req.key,
                "file_name": upload_session.original_filename,
            }
        )

        session.add(video_event)

        upload_session.status = UploadSessionStatusEnum.COMPLETED
        upload_session.completed_at = datetime.now(timezone.utc)
        upload_session.uploaded_parts_count = len(uploaded_parts) # upload_session.total_parts

        await session.commit()

    except Exception as e:
        await session.rollback()
        logger.exception("Complete upload failed")
        
        result = await session.execute(
            select(UploadSession).where(
                UploadSession.id == req.uploadSessionId,
                UploadSession.video_id == video_id    
            )
        )
        upload_session = result.scalar_one_or_none()  # scalars().first()
    
        if upload_session:
            upload_session.status = UploadSessionStatusEnum.FAILED
            await session.commit()

        raise HTTPException(status_code=500, detail=str(e))
    
    # Phase 2: Create a TranscodeTask
    try:        
        logger.info("Adding transcode task for %s", req.key)

        # Create A TranscodeTask entry
        transcode_task = TranscodeTask(
            video_id=video_id,
            # upload_session_id=req.uploadSessionId,
            status=VideoProcessingStatusEnum.PENDING,
        )

        session.add(transcode_task)
        await session.flush()   # Get transcode_task_id # INSERT happens, UUID becomes available
        await session.commit()

    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Failed creating TranscodeTask")
        raise  # I think it should raise HTTPException saying something!

    # Phase 3: Send Task to Redis
    task_id: str | None = None
    try:
        # start celery transcode task
        task = process_video_worker_operations.delay( # type: ignore
            object_key=req.key,
            video_id=video_id,
            upload_id=req.uploadId,
            upload_session_id=req.uploadSessionId,
            transcode_task_id=str(transcode_task.id),
        )
        
        task_id = str(task.id)
        # print("TASK ID: ", task.id)
        transcode_task.status = VideoProcessingStatusEnum.QUEUED
        await session.commit()

        logger.info("Task queued: %s", task.id)
    
    except (
        redis.exceptions.ConnectionError,
        kombu.exceptions.OperationalError,
        RuntimeError
    ) as e:
        # print(f"Redis task sending error: {e}")
        transcode_task.status = VideoProcessingStatusEnum.QUEUE_FAILED
        await session.commit()

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
    """

@router.post("/{video_id}/abort-upload")
async def abort_upload(
    video_id: str,
    req: AbortRequest,
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.abort(
        video_id=video_id,
        upload_id=req.uploadId,
        object_key=req.key
    )

    """
    try:
        s3.abort_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
        )

        # get video_id from upload_id
        result = await session.execute(
            select(UploadSession).where(
                UploadSession.video_upload_id == req.uploadId,
                UploadSession.video_id == video_id    
            )
        )
        upload_session = result.scalar_one_or_none()

        if not upload_session:
            raise ValueError("Upload session not found for the given upload ID")

        # Add a VideoEvent to the session
        video_event = VideoEvent(
            event_type = "CHUNKS_UPLOAD_ABORTED",
            video_id=video_id,
            # video_id = req.videoId,
            payload = {
                "upload_id": req.uploadId,
                "object_key": req.key,
                "file_name": upload_session.original_filename,
            },
        )
        session.add(video_event)

        upload_session.status = UploadSessionStatusEnum.ABORTED

        await session.commit()

        return {"success": True, "status": "aborted"}
    except Exception as e:
        return {"error": str(e)}
    """

@router.post("/{upload_id}/video/{video_id}/pause-upload")
async def pause_video_upload(video_id: str, upload_id: str, upload_service: UploadService = Depends(get_upload_service)):
    return await upload_service.pause(video_id=video_id, upload_id=upload_id)
    """
    result = await session.execute(
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

    # Add a VideoEvent to the session
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_PAUSED",
        video_id=video_id,
        payload = {
            "upload_id": upload_id,
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
        },
    )
    session.add(video_event)
        
    await session.commit()

    return { "success": True, "status": "paused"}
    """

@router.post("/{upload_id}/video/{video_id}/resume-upload")
async def resume_video_upload(video_id: str, upload_id: str, upload_service: UploadService = Depends(get_upload_service)):
    return await upload_service.resume(video_id=video_id, upload_id=upload_id)
    """
    result = await session.execute(
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
    # result = await session.execute(
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

    # Add a VideoEvent to the session
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_RESUMED",
        video_id = video_id,
        payload = {
            "upload_id": upload_id,
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,  # Assuming the key is the filename
        },
    )
    
    session.add(video_event)

    await session.commit()
    # Might need to add rollback if error occurs
    return {
        "success": True,
        "status": "resumed",
        "uploadId": upload_id,
        "uploaded_parts": uploaded_parts,
    }
    """


# Record Uploaded Part
# After a successful chunk upload, frontend sends ETag.
@router.post("/{upload_id}/video/{video_id}/record-uploaded-part")
async def record_uploaded_part(
    upload_id: str,
    video_id: str,
    part: Part,
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.record_uploaded_part(
        video_id=video_id,
        upload_id=upload_id,
        part=part,
    )

    """
    result = await session.execute(
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
        session.add(new_part)
        
        # Increment uploaded parts count by 1
        upload_session.uploaded_parts_count += 1

        # Add a VideoEvent to the session
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
        session.add(video_event)

        await session.commit()

    except IntegrityError:
        # catch it. Then simply return success. Duplicate chunk uploads are perfectly normal.
        # raise HTTPException(status=400, detail="This part has already been recorded.")
        await session.rollback() 
        return {
            "success": True,
            "message": "uploaded part already recorded"
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status=500, detail=str(e))

    return {
        "success": True,
        "message": "uploaded part recorded successfully"
    }
    """


@router.get("/{video_id}/processing-status/{transcode_task_id}")
async def get_video_processing_status(
    video_id: str,
    transcode_task_id: str,
    video_repo: VideoRepository = Depends(get_video_repository),
    transcode_repo: TranscodeRepository = Depends(get_transcode_repository),
):
    video = await video_repo.get(video_id)
    if not video:
        raise VideoNotFound()

    # if not video:
    #     raise HTTPException(status_code=404, detail=f"Video with id {video_id} not found!")
    
    if video.transcode_task_id != transcode_task_id:
        # raise HTTPException(status_code=503, detail="Task id doesn't belong to the video")
        raise TranscodeTaskMismatch()


    transcode_task = await transcode_repo.get(transcode_task_id)

    if not transcode_task:
        raise TranscodeTaskNotFound()

    # If transcode_task_id is not present
    # if not transcode_task:
    #     raise HTTPException(status_code=400, detail=f"Transcode task {transcode_task_id} not found!")

    status = AsyncResult(transcode_task_id, app=celery)

    return {
        "task_id": transcode_task_id,
        "status": status.status,
        "result": status.result,
        "progress": transcode_task.progress_percent,
    }


# Retry upload 
@router.post("/{video_id}/retry-upload")
async def retry_failed_upload(
    video_id: str,
    # session: AsyncSession = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.retry(video_id=video_id)

    """
    # Find the latest failed/paused upload session
    result = await session.execute(
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
    # result = await session.execute(stmt)
    # uploaded_parts = result.scalars().all()

    # Add a VideoEvent to the session
    video_event = VideoEvent(
        event_type = "CHUNKS_UPLOAD_RETRY",
        video_id=video_id,
        payload = {
            "upload_id": str(upload_session.video_upload_id),
            "object_key": upload_session.object_key,
            "file_name": upload_session.original_filename,
            "upload_session": str(upload_session.id),
            "uploaded_parts": len(uploaded_parts)
        },
    )
    session.add(video_event)
        
    await session.commit()

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
        "videoId": video_id,
        "uploadSessionId": str(upload_session.id),
        "uploadId": upload_session.video_upload_id,
        "objectKey": upload_session.object_key,
        "uploaded_parts": uploaded_parts,
    }
    """

    # RESTART UPLOAD
    #
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
    