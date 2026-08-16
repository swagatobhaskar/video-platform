import logging
import uuid
from fastapi.routing import APIRouter
from fastapi import Depends
# from pytz import timezone

from app.services.video_service import VideoService
from app.schemas import video_schema
from app.dependencies import get_current_user, get_db, get_video_service
from app.utils import security
from app.models import VideoPublicationStatusEnum

from app.core.config import get_settings

router = APIRouter(prefix="/api/video", tags=["video"])

settings = get_settings()

# logger = logging.getLogger(__name__)

# admin route
@router.get("/admin-view", response_model=list[video_schema.VideoAdminRead])
async def get_video_admin_view(
    status: VideoPublicationStatusEnum | None = None,
    video_service: VideoService = Depends(get_video_service),
):
    return await video_service.get_admin_view(status)


@router.patch("/{video_id}/publish", response_model=video_schema.VideoRead)
async def publish_video(
    video_id: uuid.UUID,
    video_service: VideoService = Depends(get_video_service),
):
    return await video_service.publish(video_id)


@router.patch("/{video_id}/archive")
async def archive_video(
    video_id: uuid.UUID,
    video_service: VideoService = Depends(get_video_service),
):
    return await video_service.archive(video_id)


@router.get("/require-user-action", response_model=list[video_schema.VideoActionRequiredResponse])
async def get_videos_requiring_user_action(video_service: VideoService = Depends(get_video_service)):
    return await video_service.get_videos_requiring_user_action()


@router.get("/upload-history", response_model=list[video_schema.VideoUploadHistoryRead])
async def get_upload_history(video_service: VideoService = Depends(get_video_service)):
    return await video_service.get_upload_history()
    

# Add query parameter for Draft/Published/Archived videos
@router.get("/", response_model=list[video_schema.VideoRead])
async def get_video_list(
    status: VideoPublicationStatusEnum | None = None,
    video_service: VideoService = Depends(get_video_service)
):
    return await video_service.list(status)


@router.delete("/{video_id}")
async def delete_video(video_id: uuid.UUID, video_service: VideoService = Depends(get_video_service)):
    return await video_service.delete(video_id)


# Add query parameter for Draft/Published/Archived videos
@router.get("/{video_id}", response_model=video_schema.VideoRead)
async def get_video_detail(video_id: uuid.UUID, video_service: VideoService = Depends(get_video_service)):
    return await video_service.get_detail(video_id)


@router.patch("/{video_id}/metadata", response_model=video_schema.VideoMetadataRead)
async def update_video_metadata(
    video_id: uuid.UUID,
    req: video_schema.VideoMetadataUpdate,
    video_service: VideoService = Depends(get_video_service),
):
    return await video_service.update_metadata(video_id, req)


@router.patch("/{video_id}/seo", response_model=video_schema.VideoSEORead)
async def update_video_seo_data(
    video_id: uuid.UUID,
    req: video_schema.VideoSEOUpdate,
    video_service: VideoService = Depends(get_video_service),
):
    return await video_service.update_seo(video_id, req)


@router.patch("/{video_id}/transcript")
async def update_video_transcript(
    video_id: uuid.UUID,
    video_service: VideoService = Depends(get_video_service),
):
    return await video_service.update_transcript(video_id)
