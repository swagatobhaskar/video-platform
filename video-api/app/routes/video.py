import datetime
import logging
import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from pytz import timezone
from sqlalchemy import select, exists, and_, not_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.schemas import video_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, VideoPublicationStatusEnum, UploadSession, UploadSessionStatusEnum
from app.config import get_settings

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
            selectinload(Video.upload_sessions).selectinload(UploadSession.parts),
            selectinload(Video.transcode_tasks),
            # selectinload(Video.transcode_tasks).selectinload(TranscodeTask.upload_session),
            selectinload(Video.video_events),
             # selectinload(Video.video_events).selectinload(VideoEvent.transcode_task),
        )
    )

    if status:
        stmt = stmt.where(Video.publication_status == status)

    result = await session.execute(stmt)

    return result.scalars().all()


@router.patch("/{video_id}/publish")
async def publish_video(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    stmt = await session.execute(
        select(Video)
        .options(
            selectinload(Video.upload_sessions),
            selectinload(Video.transcode_tasks),
            selectinload(Video.video_transcripts),
        )
        .where(
            Video.id == video_id,
            Video.publication_status == VideoPublicationStatusEnum.DRAFT
        )
    )

    video = stmt.scalar_one_or_none()

    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")

    if not video.can_publish:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Video cannot be published. The following fields are required.",
                "errors": video.publish_errors,
            },
        )
    try:
        video.publication_status = VideoPublicationStatusEnum.PUBLISHED

        # Do not overwrite publish date if it was already publish at a past date
        if video.published_at is None:
            video.published_at = datetime.now(timezone.utc)
        
        await session.commit()
        # await session.refresh(video)  # optional

        return {
            "message": "Video published successfully.",
            "status": video.publication_status.value,
            "published_at": video.published_at,
        }
    
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Database error. Failed to publish video %s", video_id)
        raise HTTPException(status_code=500, detail="Failed to archive video.")


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
            selectinload(Video.upload_sessions),
            selectinload(Video.transcode_tasks),
        )
        .where(
            Video.publication_status == VideoPublicationStatusEnum.DRAFT
        )
    )

    videos = stmt.scalars().all()

    response = []

    for video in videos:
        if video.can_publish:
            continue

        response.append(
            {
                "video_id": video.id,
                "title": video.title,
                "upload_status": video.upload_status,
                "transcoded": video.transcoded,
                "errors": video.publish_errors,
            }
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
        selectinload(Video.upload_sessions),
        selectinload(Video.transcode_tasks),
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
            selectinload(Video.upload_sessions),
            selectinload(Video.transcode_tasks),
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
            selectinload(Video.upload_sessions),    
            selectinload(Video.transcode_tasks),
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    return video

