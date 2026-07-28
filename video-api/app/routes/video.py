import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy import select

from app.schemas import list_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, Series, Category, VideoPublicationStatusEnum
from app.config import get_settings

router = APIRouter(prefix="/api/video", tags=["video"])

settings = get_settings()

# Add query parameter for Draft/Published/Archived videos
@router.get("/", response_model=list[list_schema.VideoListOut])
async def get_video_list(
    status: VideoPublicationStatusEnum | None = None,
    session: AsyncSession = Depends(get_db)
):
    # Get all video_ids
    query = select(Video)

    if status:
        query = query.where(Video.publication_status == status)

    result = await session.execute(query)
    videos = result.scalars().all()

    return videos


# Add query parameter for Draft/Published/Archived videos
@router.get("/{video_id}", response_model=list_schema.VideoDetailOut)
async def get_video_detail(video_id: uuid.UUID, session: AsyncSession = Depends(get_db)):

    result = await session.execute(
        select(Video).where(Video.id == video_id)
        )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found!")

    return video
