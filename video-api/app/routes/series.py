import uuid
from fastapi.routing import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from app.schemas import series_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import Video, Series
from app.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api/series", tags=["series"])

logger = logging.getLogger(__name__)


# Series list
@router.get("/", response_model=list[series_schema.SeriesListOut])
async def get_series_list(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Series))
    all_series = result.scalars().all()
    return all_series


# Series detail
@router.get("/{series_id}", response_model=series_schema.SeriesDetailOutWithVideo)
async def get_series_detail(series_id: uuid.UUID, session: AsyncSession = Depends(get_db)):

    result = await session.execute(
        select(Series).where(Series.id == series_id),
        selectinload(Video).load_only(Video.id, Video.title)
    )
    series = result.scalar_one_or_none()

    if not series:
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found!")

    return series


# Series create
@router.post("/", response_model=series_schema.SeriesDetailOut, status_code=201)
async def create_new_series(req: series_schema.SeriesCreate, session: AsyncSession = Depends(get_db)):
    try:
        new_series = Series(name=req.name)
        session.add(new_series)
        await session.commit()
        await session.refresh(new_series)

    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="A series with that name already exists.")

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error.")

    return new_series


# Series delete
# Keep the videos, just remove their category.
# Later: add option to delete the videos as well
@router.delete("/{series_id}", status_code=204)
async def delete_category(
    series_id: uuid.UUID,
    delete_videos: bool = False,
    session: AsyncSession = Depends(get_db)
):    
    series = await session.get(Series, series_id)

    if series is None:
        raise HTTPException(status_code=404, detail="Series not found")

    try:
        if delete_videos:
            await session.execute(
                delete(Video).where(Video.series_id == series_id)
            )

        await session.delete(series)
        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error")
