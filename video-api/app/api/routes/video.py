import datetime
import logging
import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from pytz import timezone
from sqlalchemy import select, exists, and_, not_, update
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.services.video_service import VideoPublishError, VideoService
from app.schemas import video_schema
from app.core.database import AsyncSession
from app.dependencies import get_current_user, get_db
from app.utils import security
from app.models import (
    Video, VideoPublicationStatusEnum, UploadSession,
    UploadSessionStatusEnum, VideoProcessingStatusEnum
)
from app.core.config import get_settings

router = APIRouter(prefix="/api/video", tags=["video"])

settings = get_settings()

logger = logging.getLogger(__name__)

# admin route
@router.get("/admin-view", response_model=list[video_schema.VideoAdminRead])
async def get_video_admin_view(
    status: VideoPublicationStatusEnum | None = None,
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Video)
        .options(
            selectinload(Video.upload_session).selectinload(UploadSession.parts),
            selectinload(Video.transcode_task),
            # selectinload(Video.transcode_tasks).selectinload(TranscodeTask.upload_session),
            selectinload(Video.video_events),
             # selectinload(Video.video_events).selectinload(VideoEvent.transcode_task),
        )
    )

    if status:
        stmt = stmt.where(Video.publication_status == status)

    result = await session.execute(stmt)

    return result.scalars().all()


@router.patch("/{video_id}/publish", response_model=video_schema.VideoRead)
async def publish_video(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    stmt = await session.execute(
        select(Video)
        .options(
            selectinload(Video.category),
            selectinload(Video.series),
            selectinload(Video.upload_session),
            selectinload(Video.transcode_task),
            selectinload(Video.video_transcripts),
        )
        .where(
            Video.id == video_id,
            Video.publication_status.in_([
                VideoPublicationStatusEnum.DRAFT,
                VideoPublicationStatusEnum.ARCHIVED,
            ])  
        )
    )

    video = stmt.scalar_one_or_none()

    if video is None:
        raise HTTPException(status_code=404, detail="Video not found or already published.")

    video_service = VideoService(video, session)

    try:
        await video_service.publish()
        
    except VideoPublishError as exc:
        raise HTTPException(status_code=400, detail=exc.errors)

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Failed to publish video.")

    return video
    # return {
    #     "message": "Video published successfully.",
    #     "status": video.publication_status.value,
    #     "published_at": video.published_at,
    # }


@router.patch("/{video_id}/archive")
async def archive_video(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    try:
        result = await session.execute(
            update(Video)
            .where(
                Video.id == video_id,
                Video.publication_status == VideoPublicationStatusEnum.PUBLISHED
            )
            .values(publication_status=VideoPublicationStatusEnum.ARCHIVED)
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Video not found or video is not published.")

        await session.commit()

        return {
            "message": "Video archived successfully.",
            "status": "archived",
        }
    
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Database error. Failed to archive video %s", video_id)
        raise HTTPException(status_code=500, detail="Failed to archive video.")


@router.get("/require-user-action", response_model=list[video_schema.VideoActionRequiredResponse])
async def get_videos_requiring_user_action(session: AsyncSession = Depends(get_db)):
    stmt = await session.execute(
        select(Video)
        .options(
            selectinload(Video.upload_session),
            selectinload(Video.transcode_task),
        )
        .where(
            Video.publication_status == VideoPublicationStatusEnum.DRAFT
        )
    )

    videos = stmt.scalars().all()

    response = []
    
    for video in videos:
        video_service = VideoService(video, session)
        if video_service.can_publish:
            continue

        response.append(
            {
                "video_id": video.id,
                "title": video.title,
                "upload_status": video_service.upload_status,
                "transcoded": video_service.transcoded,
                "errors": video_service.publish_errors,
            }
        )

    return response



@router.get("/upload-history", response_model=list[video_schema.VideoUploadHistoryRead])
async def get_upload_history(session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Video)
        .options(
            # Since UploadSession and TranscodeTask are now one-to-one, you can also consider joinedload.
            joinedload(Video.upload_session),
            joinedload(Video.transcode_task)
        )
    )

    videos = result.scalars().all()
    
    response = []

    for video in videos:
        response.append(
            video_schema.VideoUploadHistoryRead(
                **video_schema.VideoUploadHistoryRead.model_validate(video).model_dump(),
                video_status=video.upload_status,
                progress_percent=video.task_progress_percent,
            )
        )
        
    return response
    

# Add query parameter for Draft/Published/Archived videos
@router.get("/", response_model=list[video_schema.VideoRead])
async def get_video_list(
    status: VideoPublicationStatusEnum | None = None,
    session: AsyncSession = Depends(get_db)
):
    # Get all video_ids
    query = select(Video).options(
        selectinload(Video.category),
        selectinload(Video.series),
        selectinload(Video.video_transcripts),
        selectinload(Video.upload_session),
        selectinload(Video.transcode_task),
    )

    if status:
        query = query.where(Video.publication_status == status)

    result = await session.execute(query)
    return result.scalars().all()


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    stmt = await session.execute(
        select(Video)
        .options(
            selectinload(Video.upload_session),
            selectinload(Video.transcode_task),
        )
        .where(Video.id == video_id)
    )

    video = stmt.scalar_one_or_none()

    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")

    # Save storage keys before deleting DB object
    object_key = video.object_key
    thumbnail_key = video.thumbnail_object_key

    await session.delete(video)
    await session.commit()

    # Delete objects from storage after successful DB delete
    # await storage.delete_video_files(object_key, thumbnail_key)

    return {
        "message": "Video deleted successfully.",
        "video_id": str(video_id),
    }


# Add query parameter for Draft/Published/Archived videos
@router.get("/{video_id}", response_model=video_schema.VideoRead)
async def get_video_detail(video_id: uuid.UUID, session: AsyncSession = Depends(get_db)):

    result = await session.execute(
        select(Video).where(Video.id == video_id)
        .options(
            selectinload(Video.category),
            selectinload(Video.series),
            selectinload(Video.video_transcripts),
            selectinload(Video.upload_session),    
            selectinload(Video.transcode_task),
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    return video


@router.patch("/{video_id}/metadata", response_model=video_schema.VideoMetadataRead)
async def update_video_metadata(
    video_id: uuid.UUID,
    req: video_schema.VideoMetadataUpdate,
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Video)
        .options(
            selectinload(Video.category),
            selectinload(Video.series),
            selectinload(Video.video_transcripts),
        )
        .where(Video.id == video_id)
    )

    result = await session.execute(stmt)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found.")

    video_service = VideoService(video, session)

    # Without exclude_unset=True, PATCH requests may overwrite
    # existing fields with NULL.
    update_data = req.model_dump(exclude_unset=True)

    try:
        # Without exclude_unset=True, you would accidentally overwrite existing values with NULL.
        await video_service.update_data(data = update_data)

        return video

    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Invalid data. Update violates database constraints.")

    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Database error while updating video %s", video_id)
        raise HTTPException(status_code=500, detail="Failed to update video.")
    

@router.patch("/{video_id}/seo", response_model=video_schema.VideoSEORead)
async def update_video_seo_data(
    video_id: uuid.UUID,
    req: video_schema.VideoSEOUpdate,
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Video)
        .options(selectinload(Video.video_transcripts))
        .where(Video.id == video_id)
    )

    result = await session.execute(stmt)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found.")

    video_service = VideoService(video, session)

    # Without exclude_unset=True, PATCH requests may overwrite
    # existing fields with NULL.
    seo_data = req.model_dump(exclude_unset=True)

    try:
        # Without exclude_unset=True, you would accidentally overwrite existing values with NULL.
        await video_service.update_data(data = seo_data)

        return video

    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Database error while updating video %s", video_id)
        raise HTTPException(status_code=500, detail="Failed to update video.")


@router.patch("/{video_id}/transcript")
async def update_video_transcript(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Video)
        .options(selectinload(Video.video_transcripts))
        .where(Video.id == video_id)
    )

    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

