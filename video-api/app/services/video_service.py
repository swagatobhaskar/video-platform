from datetime import datetime, timezone, UTC
from app.database.session import AsyncSession
from app.database.models import (
    Video, UploadSessionStatusEnum, VideoPublicationStatusEnum,
    VideoProcessingStatusEnum, UploadSession, TranscodeTask
)

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
        self.errors = errors
        super().__init__("Video cannot be published.")

class VideoService:

    def __init__(self, video: Video, session: AsyncSession):
        self.video = video
        self.session = session

    @property
    def video_uploaded(self) -> bool:
        return any(
            session.status == UploadSessionStatusEnum.COMPLETED
            for session in self.video.upload_sessions
        )

    @property
    def thumbnail_uploaded(self) -> bool:
        return bool(self.video.thumbnail_object_key)

    @property
    def transcript_uploaded(self) -> bool:
        return any(t.transcript_text for t in self.video.video_transcripts)

    @property
    def latest_transcode_task(self) -> TranscodeTask | None:
        if not self.video.transcode_tasks:
            return None

        return max(
            self.video.transcode_tasks,
            key=lambda t: t.created_at,
        )

    @property
    def transcoded(self) -> bool:
        task = self.latest_transcode_task
        return (task is not None and task.status == VideoProcessingStatusEnum.COMPLETED)

    @property
    def latest_upload_session(self) -> UploadSession | None:
        if not self.video.upload_sessions:
            return None

        return max(
            self.video.upload_sessions,
            key=lambda x: x.created_at
        )

    @property
    def upload_status(self) -> str | None:
        session = self.latest_upload_session

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

        await self.session.commit()
        await self.session.refresh(self.video)


    async def archive(self):
        pass