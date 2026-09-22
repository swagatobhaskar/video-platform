import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.database.models import (
    User, Video, VideoPublicationStatusEnum, Series, Category, UploadSession, UploadSessionStatusEnum,
    VideoEvent, VideoTranscript, VideoProcessingStatusEnum, TranscodeTask
)

