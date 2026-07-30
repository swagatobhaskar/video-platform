from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime


class SeriesBase(BaseModel):
    name: str


class SeriesCreate(SeriesBase):
    pass


class SeriesUpdate(BaseModel):
    name: str | None = None


class SeriesListOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class SeriesDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class SeriesAssociatedVideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # These are fields for Video
    id: uuid.UUID
    title: str | None = None


class SeriesDetailOutWithVideo(SeriesBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    videos: list[SeriesAssociatedVideoOut] = []
    