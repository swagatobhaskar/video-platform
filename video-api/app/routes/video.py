import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.schemas import video_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, VideoPublicationStatusEnum, UploadSession
from app.config import get_settings

router = APIRouter(prefix="/api/video", tags=["video"])

settings = get_settings()

# Add query parameter for Draft/Published/Archived videos
@router.get("/", response_model=list[video_schema.VideoSummary])
async def get_video_list(
    status: VideoPublicationStatusEnum | None = None,
    session: AsyncSession = Depends(get_db)
):
    # Get all video_ids
    query = select(Video).options(
        selectinload(Video.category),
        selectinload(Video.series), 
    )

    if status:
        query = query.where(Video.publication_status == status)

    # need to fetch related models

    result = await session.execute(query)
    return result.scalars().all()


# Add query parameter for Draft/Published/Archived videos
@router.get("/{video_id}", response_model=video_schema.VideoRead)
async def get_video_detail(video_id: uuid.UUID, session: AsyncSession = Depends(get_db)):

    result = await session.execute(
        select(Video).where(Video.id == video_id)
        .options(
            selectinload(Video.category),
            selectinload(Video.series),
            selectinload(Video.video_transcripts),
            selectinload(Video.upload_sessions).selectinload(UploadSession.parts),
            selectinload(Video.transcode_tasks),
            # selectinload(Video.transcode_tasks).selectinload(TranscodeTask.upload_session)
            selectinload(Video.video_events),
            # selectinload(Video.video_events).selectinload(VideoEvent.transcode_task)
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    return video
