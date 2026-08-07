
from datetime import datetime, timezone, UTC
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from slugify import slugify
import logging
import uuid

from app.database.session import AsyncSession
from app.database.models import (
    Video, UploadSessionStatusEnum, VideoPublicationStatusEnum,
    VideoProcessingStatusEnum, UploadSession, TranscodeTask
)

logger = logging.getLogger(__name__)

REQUIRED_SEO_FIELDS = (
    "search_intent",
    "focus_keyword",
    "keywords",
    "seo_tags",
    "seo_summary_en",
    "secondary_keywords",
    "thumbnail_alt_text",
    "meta_description",
    "meta_title",
)

class VideoPublishError(Exception):
    def __init__(self, errors: dict[str, list[str]]):
        super().__init__("Video cannot be published.")
        self.errors = errors

# No session.
# No repository.
# No SQLAlchemy queries.
# No commit.
# Only things that depends only on the Video object.

class VideoManager:
    def __init__(self, video: Video):
        self.video = video

    # def __init__(self, video: Video, session: AsyncSession):
    #     self.video = video
    #     self.session = session

    @property
    def video_uploaded(self) -> bool:
        # return any(
        #     session.status == UploadSessionStatusEnum.COMPLETED
        #     for session in self.video.upload_sessions
        # )
        return self.video.upload_session.status == UploadSessionStatusEnum.COMPLETED

    @property
    def thumbnail_uploaded(self) -> bool:
        return bool(self.video.thumbnail_object_key)

    @property
    def transcript_uploaded(self) -> bool:
        return any(t.transcript_text for t in self.video.video_transcripts)

    # @property
    # def latest_transcode_task(self) -> TranscodeTask | None:
    #     if not self.video.transcode_tasks:
    #         return None

    #     return max(
    #         self.video.transcode_tasks,
    #         key=lambda t: t.created_at,
    #     )

    @property
    def transcoded(self) -> bool:
        # task = self.latest_transcode_task
        task = self.video.transcode_task
        return (task is not None and task.status == VideoProcessingStatusEnum.COMPLETED)

    # @property
    # def latest_upload_session(self) -> UploadSession | None:
    #     if not self.video.upload_sessions:
    #         return None

    #     return max(
    #         self.video.upload_sessions,
    #         key=lambda x: x.created_at
    #     )

    @property
    def upload_status(self) -> str | None:
        # session = self.latest_upload_session
        session = self.video.upload_session

        if not session:
            return None

        return session.status.value

    @property
    def missing_metadata_fields(self) -> list[str]:
        missing = []

        if not self.video.title:
            missing.append("title")

        if not self.video.description:
            missing.append("description")

        if not self.video.slug:
            missing.append("slug")

        if self.video.category_id is None:
            missing.append("category_id")

        if self.video.language is None:
            missing.append("language")

        return missing
    
    @property
    def missing_seo_fields(self) -> list[str]:
        missing = []

        for field in REQUIRED_SEO_FIELDS:
            value = getattr(self.video, field)

            if value in (None, "", []): #[None, "", []]:
                missing.append(field)

        return missing

    @property
    def publish_errors(self) -> dict[str, list[str]]:

        errors = {}

        if not self.video_uploaded:
            errors["video"] = ["Video has not been uploaded."]

        if not self.transcoded:
            errors["processing"] = ["Video processing incomplete."]

        if not self.thumbnail_uploaded:
            errors["thumbnail"] = ["Thumbnail missing."]

        missing_metadata = self.missing_metadata_fields
        if missing_metadata:
            errors["metadata"] = missing_metadata

        missing_seo = self.missing_seo_fields
        if missing_seo:
            errors["seo"] = missing_seo

        return errors

    @property
    def can_publish(self) -> bool:
        return not self.publish_errors


    async def publish(self):
        if not self.can_publish:
            # raise ValueError(f"Video cannot be published: {self.publish_errors}")
            raise VideoPublishError(self.publish_errors)

        self.video.publication_status = VideoPublicationStatusEnum.PUBLISHED
        self.video.published_at = datetime.now(UTC)

        # VideoManager wont commit
        #
        # try:
        #     await self.session.commit()
        #     await self.session.refresh(self.video)
        # except SQLAlchemyError:
        #     await self.session.rollback()
        #     logger.exception("Database Error. Video publish failed!")
        #     raise # HTTPException(status_code=500, detail="Failed to publish video.")


    async def slug_exists(self, slug: str, exclude_video_id: uuid.UUID | None = None) -> bool:
        # Look for a video with the given slug.
        stmt = select(Video.id).where(Video.slug == slug)

        # Ignore the current video when updating an existing record.
        # Otherwise, the query would always find the current video's slug
        # and incorrectly report it as a duplicate.
        if exclude_video_id is not None:
            stmt = stmt.where(Video.id != exclude_video_id)

        result = await self.session.execute(stmt)

        # Return True if any matching video exists.
        return result.scalar_one_or_none() is not None


    async def generate_unique_slug(self, title: str) -> str:
        # Convert the title into a URL-friendly slug.
        # Example:
        #   "My First Video!" -> "my-first-video"
        base_slug = slugify(title)

        # If the title contains only punctuation, emojis, or other
        # characters that cannot form a slug, use a generic fallback.
        if not base_slug:
            base_slug = "video"

        # Try the base slug first.
        slug = base_slug

        # Suffix numbering starts at 2:
        #   my-video
        #   my-video-2
        #   my-video-3
        counter = 2

        # Keep incrementing the suffix until an unused slug is found.
        while await self.slug_exists(
            slug,
            exclude_video_id=self.video.id,
        ):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Return the first available unique slug.
        return slug


    # Used for metadata and SEO update
    async def update_data(self, data: dict):
        # If the client included a slug in the PATCH request,
        # normalize and validate it.
        if "slug" in data:
            # Convert None to an empty string and remove leading/trailing whitespace.
            slug = (data["slug"] or "").strip()

            # If the slug is empty, regenerate it from the current title.
            if not slug:
                # Slug generation requires a title.
                # This should rarely happen, but guard against it anyway.
                if not self.video.title:
                    raise ValueError(
                        "Cannot generate slug because the video has no title."
                    )

                # Generate a unique slug using the title already stored in the database.
                data["slug"] = await self.generate_unique_slug(self.video.title)
            else:
                # Store the cleaned-up slug back into the update payload.
                data["slug"] = slug

        # If the client changed the title but didn't explicitly provide a slug,
        # automatically regenerate the slug from the new title.
        elif "title" in data:
            data["slug"] = await self.generate_unique_slug(data["title"])

        # If we're about to save a slug (either user-provided or auto-generated),
        # ensure no other video already uses it.
        if "slug" in data:
            if await self.slug_exists(
                data["slug"],
                exclude_video_id=self.video.id,
            ):
                raise ValueError("Slug already exists.")

        # Apply every updated field to the SQLAlchemy model.
        for field, value in data.items():
            setattr(self.video, field, value)

        # Persist the changes to the database.
        await self.session.commit()

        # Reload the object so database-generated values (timestamps, etc.)
        # are reflected on the model instance.
        await self.session.refresh(self.video)

        # Return the updated video.
        return self.video
    