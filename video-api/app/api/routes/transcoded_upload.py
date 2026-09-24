import logging
from fastapi import APIRouter, Depends

from app.dependencies import get_upload_service, get_video_repository, get_transcode_repository

from app.core.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/video/transcoded-upload", tags=["video", "transcoded-upload"])

logger = logging.getLogger(__name__)

@router.post("/{video_id}/initiate")
async def initiate_transcoded_upload(
    video_id: UUID,
    upload_service: TranscodedUploadService = Depends(get_transcoded_upload_service),
):
    return await upload_service.initiate(video_id=video_id)

@router.post("/{video_id}/presign")
async def presign_transcoded_files(
    video_id: UUID,
    req: PresignTranscodedFilesRequest,
    upload_service: TranscodedUploadService = Depends(get_transcoded_upload_service),
):
    return await upload_service.get_presigned_urls(
        video_id=video_id,
        upload_session_id=req.upload_session_id,
        files=req.files,
    )

@router.post("/{video_id}/record-uploaded-file")
async def record_uploaded_file(
    video_id: UUID,
    req: RecordUploadedFileRequest,
    upload_service: TranscodedUploadService = Depends(get_transcoded_upload_service),
):
    return await upload_service.record_uploaded_file(
        video_id=video_id,
        upload_session_id=req.upload_session_id,
        file_id=req.file_id,
    )

@router.post("/{video_id}/pause")
async def pause_transcoded_upload(
    video_id: UUID,
    upload_session_id: UUID,
    upload_service: TranscodedUploadService = Depends(get_transcoded_upload_service),
):
    return await upload_service.pause(
        video_id=video_id,
        upload_session_id=upload_session_id,
    )

@router.post("/{video_id}/resume")
async def resume_transcoded_upload(
    video_id: UUID,
    upload_session_id: UUID,
    upload_service: TranscodedUploadService = Depends(get_transcoded_upload_service),
):
    return await upload_service.resume(
        video_id=video_id,
        upload_session_id=upload_session_id,
    )

@router.post("/{video_id}/complete")
async def complete_transcoded_upload(
    video_id: UUID,
    req: CompleteTranscodedUploadRequest,
    upload_service: TranscodedUploadService = Depends(get_transcoded_upload_service),
):
    return await upload_service.complete(
        video_id=video_id,
        upload_session_id=req.upload_session_id,
    )
