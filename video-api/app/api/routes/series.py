import uuid
from fastapi.routing import APIRouter
from fastapi import status, Depends
# from sqlalchemy import select, delete
# from sqlalchemy.orm import selectinload
# from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from app.schemas import series_schema
from app.services.series_service import SeriesService
from app.dependencies import get_current_user, get_series_service

# from app.core.config import get_settings
# settings = get_settings()

router = APIRouter(prefix="/api/series", tags=["series"])

logger = logging.getLogger(__name__)


# Series list
@router.get("/", response_model=list[series_schema.SeriesOut])
async def get_series_list(series_service: SeriesService = Depends(get_series_service)):
    return await series_service.list()
    # result = await session.execute(select(Series))
    # all_series = result.scalars().all()
    # return all_series


# Series detail
@router.get("/{series_id}", response_model=series_schema.SeriesDetailOutWithVideo)
async def get_series_detail(series_id: uuid.UUID, series_service: SeriesService = Depends(get_series_service)):
    return await series_service.get_series_detail(series_id)
    """
    result = await session.execute(
        select(Series)
        .options(selectinload(Series.videos).load_only(Video.id, Video.title))
        .where(Series.id == series_id)
    )
    series = result.scalar_one_or_none()

    if not series:
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found!")

    return series
    """

# Series create
@router.post("/", response_model=series_schema.SeriesDetailOut, status_code=201)
async def create_new_series(req: series_schema.SeriesCreate, series_service: SeriesService = Depends(get_series_service)):
    return await series_service.create(name=req.name)
    """
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
    """

# Series delete
# Keep the videos, just remove their series.
# Later: add option to delete the videos as well
@router.delete("/{series_id}", status_code=204)
async def delete_series(
    series_id: uuid.UUID,
    delete_videos: bool = False,
    series_service: SeriesService = Depends(get_series_service)
):
    return await series_service.delete(id=series_id, delete_videos=delete_videos)
    """
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
    """

# Series patch
@router.patch("/{series_id}", response_model=series_schema.SeriesDetailOut)
async def update_series(
    series_id: uuid.UUID,
    req: series_schema.SeriesUpdate,
    series_service: SeriesService = Depends(get_series_service),
):
    return await series_service.update(series_id, req.name)
    """
    series = await session.get(Series, series_id)

    if series is None:
        raise HTTPException(404, "Series not found")

    if req.name is not None:
        series.name = req.name

    try:
        await session.commit()
        await session.refresh(series)

    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Series name already exists")

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(500, "Database error")

    return series
    """


# Add video to series
@router.post("/{series_id}/video/{video_id}/{episode_number}", response_model=series_schema.SeriesDetailOutWithVideo)
async def add_video_to_series(
    series_id: uuid.UUID,
    video_id: uuid.UUID,
    episode_number: int | None = None,
    series_service: SeriesService = Depends(get_series_service),
):
    return await series_service.add_video_to_series(series_id, video_id, episode_number)
    """
    series = await session.get(Series, series_id)
    if series is None:
        raise HTTPException(404, "Series not found")

    video = await session.get(Video, video_id)
    if video is None:
        raise HTTPException(404, f"Video not found")

    if video.series_id is not None:
        raise HTTPException(status_code=409, detail="Video already belongs to a series.")

    video.series = series

    # Need to check the logic
    if episode_number:
        video.episode_number = episode_number

    # or:
    # video.series_id = series.id
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Integrity constraint violated")
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(500, "Database error")

    # this doesn't match I think!
    result = await session.execute(
        select(Series)
        .options(
            selectinload(Series.videos)
            .load_only(Video.id, Video.title, Video.episode_number)
        )
        .where(Series.id == series_id)
    )

    return result.scalar_one()
    """

# Remove video from a series
@router.delete("/{series_id}/video/{video_id}", response_model=series_schema.SeriesDetailOutWithVideo)
async def remove_video_from_series(
    series_id: uuid.UUID,
    video_id: uuid.UUID,
    series_service: SeriesService = Depends(get_series_service),
):
    return await series_service.remove_video_from_series(series_id, video_id)
    """
    series = await session.get(Series, series_id)

    if series is None:
        raise HTTPException(404, "Series not found")
    
    video = await session.get(Video, video_id)

    if video is None:
        raise HTTPException(404, "Video not found")

    if video.series_id != series_id:
        raise HTTPException(400, "Video is not in this series")

    # Remove relationship
    video.series = None
    # or:
    # video.series_id = None

    try:
        await session.commit()

    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Could not remove video from series")

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(500, "Database error")

    # Reload series with videos relationship populated
    result = await session.execute(
        select(Series)
        .options(selectinload(Series.videos).load_only(Video.id, Video.title))
        .where(Series.id == series_id)
    )

    return result.scalar_one()
    """
