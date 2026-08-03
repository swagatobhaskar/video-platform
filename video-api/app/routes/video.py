import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy import select, exists, and_, not_
from sqlalchemy.orm import selectinload

from app.schemas import video_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, VideoPublicationStatusEnum, UploadSession, UploadSessionStatusEnum
from app.config import get_settings

router = APIRouter(prefix="/api/video", tags=["video"])

settings = get_settings()


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


@router.get("/requiring-user-action")
async def get_videos_requiring_user_action(session: AsyncSession = Depends(get_db)):
    # get the videos whose sate is draft and whose upload_sessions.status is not completed or aborted
    # can_publish is a Python @property, so SQLAlchemy can't translate it into SQL.
    # i.e., we can't use it in a query filter. So we need to use the actual conditions that define can_publish.
    upload_session_exists = (
        select(UploadSession.id)
        .where(
            UploadSession.video_id == Video.id,
            UploadSession.status !=
        )
        .exists()
    )

    stmt = select(Video).where(
        Video.publication_status == VideoPublicationStatusEnum.DRAFT,
        not_(
            and_(
                uploaded_session_exists,
            )
        )
    )

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
    )

    if status:
        query = query.where(Video.publication_status == status)

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
            selectinload(Video.upload_sessions),         
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    return video

