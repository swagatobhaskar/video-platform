import logging

from app.models import (
    Video, UploadSessionStatusEnum, VideoPublicationStatusEnum,
    VideoProcessingStatusEnum
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

# VideoManager answers questions about one Video.
# No session.
# No repository.
# No SQLAlchemy queries.
# No commit.
# Only things that depends only on the Video object.

# The methods with @property decorator: They all essentially answer a question about the current state of the video.
# So this is natural:
# manager.can_publish
# manager.transcoded

# rather than:
# manager.can_publish()
# manager.transcoded()
# That's exactly what @property is useful for.

# What should not be @property?
# Your methods that actually do something should remain normal methods.
# For example: slug_exists(), generate_unique_slug() should remain a method.
# Likewise: async def update_data(...) should definitely be a normal method
# because you're asking it to perform an operation.


class VideoManager:
    def __init__(self, video: Video):
        self.video = video

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
        upload_session = self.video.upload_session

        if not upload_session:
            return None

        return upload_session.status.value

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
    