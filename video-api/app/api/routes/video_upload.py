import logging
from fastapi import APIRouter, Depends
from celery.result import AsyncResult

from app.dependencies import get_upload_service, get_video_repository, get_transcode_repository
from app.workers.celery_worker import celery
from app.schemas.r2_upload_schema import CompleteRequest, Part, PartRequest, InitiateUploadRequest, AbortRequest
from app.exceptions.video import VideoNotFound
from app.exceptions.transcodetask import TranscodeTaskMismatch, TranscodeTaskNotFound
from app.repositories.video_repository import VideoRepository
from app.repositories.transcode_repository import TranscodeRepository
from app.services.upload_service import UploadService

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
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.initiate(
        content_type=req.contentType,
        file_name=req.fileName,
        upload_session_id=req.uploadSessionId,
        video_id=video_id,
        file_size_bytes=req.fileSizeBytes,
        total_parts=req.totalParts,
    )
 

@router.post("/{video_id}/get-presigned-url")
async def get_presigned_url(
    video_id: str,
    req: PartRequest,
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.get_presigned_url(
        upload_id=req.uploadId,
        object_key=req.key,
        part_number=req.partNumber
    )


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
        object_key=req.key,
        parts=req.parts,
    )
    """
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

# cancel A.K.A abort
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


@router.post("/{upload_id}/video/{video_id}/pause-upload")
async def pause_video_upload(video_id: str, upload_id: str, upload_service: UploadService = Depends(get_upload_service)):
    return await upload_service.pause(video_id=video_id, upload_id=upload_id)


@router.post("/{upload_id}/video/{video_id}/resume-upload")
async def resume_video_upload(video_id: str, upload_id: str, upload_service: UploadService = Depends(get_upload_service)):
    return await upload_service.resume(video_id=video_id, upload_id=upload_id)


# Record Uploaded Part. After a successful chunk upload, frontend sends ETag.
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

    if video.transcode_task_id != transcode_task_id:
        raise TranscodeTaskMismatch()

    transcode_task = await transcode_repo.get(transcode_task_id)

    if not transcode_task:
        raise TranscodeTaskNotFound()

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
