from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import cast

from app.schemas import list_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import User, Video, UploadSession
from app.config import get_settings

router = APIRouter(prefix="/api/list", tags=["list"])

settings = get_settings()

@router.get("/videos", response_model=list[list_schema.VideoListOut])
async def get_video_list(session: AsyncSession = Depends(get_db)):

    # Get all video_ids
    result = await session.execute(select(Video))
    videos = result.scalars().all()

    # FastAPI/Pydantic automatically serializes and calculates the computed URLs for each video item
    return videos

