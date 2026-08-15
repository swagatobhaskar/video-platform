from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator
from fastapi import Request, HTTPException, status, Depends
from jose import JWTError, jwt
import uuid
from functools import lru_cache

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.database import AsyncSession
from app.models import User

from app.services.storage.base import create_s3_client
from app.services.storage.image_service import ImageProcessor, ImageStorage
from app.services.upload_service import UploadService
from app.services.category_service import CategoryService
from app.services.series_service import SeriesService

from app.repositories.upload_repository import UploadRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.transcode_repository import TranscodeRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.series_repository import SeriesRepository

settings = get_settings()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        

def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(token: str = Depends(get_token_from_cookie), session: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")    # payload.get() can potentially return None
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
    
    user_result = await session.execute(
        select(User)
        .where(User.id == uuid.UUID(user_id))
    )
        
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user


def verify_csrf(request: Request):
    # print("verify_csrf- headers: ", request.headers)
    csrf_cookie = request.cookies.get('csrf_token')
    csrf_header = request.headers.get('X-CSRF-Token')
    # print(f"CSRF HEADER: {csrf_header} | CSRF COOKIE: {csrf_cookie} | [{csrf_header == csrf_cookie}]")
    
    if not csrf_cookie or not csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token not found!")

    if csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token! Value does not match with X-CSRF-Header!"
        )


def get_upload_repository(session: AsyncSession = Depends(get_db)) -> UploadRepository:
    return UploadRepository(session)

def get_upload_service(
    repo: UploadRepository = Depends(get_upload_repository),
    session: AsyncSession = Depends(get_db)
) -> UploadService:
    return UploadService(repo, session)

def get_video_repository(session: AsyncSession = Depends(get_db)) -> VideoRepository:
    return VideoRepository(session)

def get_transcode_repository(session: AsyncSession = Depends(get_db)) -> TranscodeRepository:
    return TranscodeRepository(session)

def get_category_repository(session: AsyncSession = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(session)

def get_image_storage():
    return ImageStorage(client=get_s3_client())

def get_image_processor():
    return ImageProcessor(storage=get_image_storage())

def get_category_service(
    session: AsyncSession = Depends(get_db),
    category_repo: CategoryRepository = Depends(get_category_repository),
    image_service: ImageStorage = Depends(get_image_storage),
    image_storage: ImageStorage = Depends(get_image_storage)
) -> CategoryService:
    return CategoryService(
        session=session,
        category_repo=category_repo,
        image_service=image_service,
        image_storage=image_storage,
    )


def get_series_repository(
    video_repo: VideoRepository,
    session: AsyncSession = Depends(get_db),
) -> SeriesRepository:
    return SeriesRepository(session=session, video_repo=video_repo)

def get_series_service(
    session: AsyncSession = Depends(get_db),
    series_repo: SeriesRepository = Depends(get_series_repository),
) -> SeriesService:
    return SeriesService(session=session, series_repo=series_repo)


@lru_cache
def get_s3_client():
    return create_s3_client()


def get_image_storage():
    return ImageStorage(client=get_s3_client())

