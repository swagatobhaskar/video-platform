from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    image_url: str | None = None

    # Client do not send the following fields. So don't include them in the base schema
    # id: uuid.UUID
    # created_at: datetime
    # updated_at: datetime

class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    image_url: str | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class CategoryVideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # These are fields for Video
    id: uuid.UUID
    title: str | None = None
    # thumbnail_url: str | None = None


class CategoryOutWithVideo(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime
    videos: list[CategoryVideoOut] = []
    