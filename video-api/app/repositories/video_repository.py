from slugify import slugify
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, joinedload

from app.core.database import AsyncSession
from app.models import Video, VideoPublicationStatusEnum, UploadSession, TranscodeTask


class VideoRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # pagination later
    async def list(self) -> list[Video]:
        result = await self.session.execute(select(Video))
        return result.scalars().all()

    async def list_videos(self, status: VideoPublicationStatusEnum | None = None):
        query = select(Video).options(
            selectinload(Video.category),
            selectinload(Video.series),
            selectinload(Video.video_transcripts),
            selectinload(Video.upload_session),
            selectinload(Video.transcode_task),
        )

        if status is not None:
            query = query.where(Video.publication_status == status)

        result = await self.session.execute(query)
        return result.scalars().all()
    

    async def get(self, video_id: UUID) -> Video | None:
        result = await self.session.execute(
            select(Video).where(Video.id == video_id)
        )
        return result.scalar_one_or_none()

    async def get_video_detail(self, id: UUID):
        result = await self.session.execute(
            select(Video).where(Video.id == id)
            .options(
                selectinload(Video.category),
                selectinload(Video.series),
                selectinload(Video.video_transcripts),
                selectinload(Video.upload_session),    
                selectinload(Video.transcode_task),
            )
        )
        return result.scalar_one_or_none()

    
    async def create(
        self,
        title: str | None = None,
        publication_status: VideoPublicationStatusEnum = VideoPublicationStatusEnum.DRAFT,
        **extra
    ) -> Video:
        video = Video(
            title=title,
            publication_status=publication_status,
            **extra
        )
        self.session.add(video)
        # await self.session.commit()
        # await self.session.refresh(video)
        await self.session.flush()
        return video


    async def update(self, video_id: UUID, **data) -> Video | None:
        video = await self.get(video_id)

        if not video:
            return None

        for key, value in data.items():
            setattr(video, key, value)

        await self.session.flush()
        # the repository doesn't need to know about the rollback. The transaction handles it.
        return video

    """
    Why flush() instead of commit()?
    If create_video() commits...
    ...and create_upload_session() commits...
    ...and create_event() commits...
    ...you've lost the ability to roll everything back as one unit.
    The service should own the transaction.
    """


    async def get_for_delete(self, video_id: UUID) -> Video | None:
        result = await self.session.execute(
            select(Video)
            .options(
                selectinload(Video.upload_session),
                selectinload(Video.transcode_task),
            )
            .where(Video.id == video_id)
        )

        return result.scalar_one_or_none()

    async def delete(self, video: Video) -> None:
        await self.session.delete(video)
        await self.session.flush()


    # Specialized query methods. They exist to avoid the N+1 query problem and unnecessary lazy loading in SQLAlchemy.
    # Instead, you can eagerly load the relationship.
    async def get_with_upload_session(self, video_id: UUID) -> Video | None:
        result = await self.session.execute(
            select(Video)
            .options(selectinload(Video.upload_session))
            .where(Video.id == video_id)
        )
        return result.scalar_one_or_none()


    async def get_with_transcode(self, video_id: UUID):
        result = await self.session.execute(
            select(Video)
            .options(selectinload(Video.transcode_task))
            .where(Video.id == video_id)
        )

        return result.scalar_one_or_none()


    async def get_upload_history(self) -> list[Video]:
        result = await self.session.execute(
            select(Video)
            .options(
                # selectinload(Video.category),
                # selectinload(Video.series),
                selectinload(Video.upload_session).load_only(UploadSession.status),
                selectinload(Video.transcode_task).load_only(TranscodeTask.status, TranscodeTask.progress_percent),
            )
        )
        return result.scalars().all()

    async def get_with_events(self, video_id: UUID):
        pass

    async def get_for_player(self, video_id: UUID):
        pass

    async def get_for_admin(self, status: VideoPublicationStatusEnum):
        stmt = (
            select(Video)
            .options(
                selectinload(Video.upload_session).selectinload(UploadSession.parts),
                selectinload(Video.transcode_task),
                # selectinload(Video.transcode_tasks).selectinload(TranscodeTask.upload_session),
                selectinload(Video.video_events),
                # selectinload(Video.video_events).selectinload(VideoEvent.transcode_task),
            )
        )
    
        if status:
            stmt = stmt.where(Video.publication_status == status)
    
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unpublished_video(self, id: UUID):
        result = await self.session.execute(
            select(Video)
            .options(
                selectinload(Video.category),
                selectinload(Video.series),
                selectinload(Video.upload_session),
                selectinload(Video.transcode_task),
                selectinload(Video.video_transcripts),
            )
            .where(
                Video.id == id,
                Video.publication_status.in_([
                    VideoPublicationStatusEnum.DRAFT,
                    VideoPublicationStatusEnum.ARCHIVED,
                ])  
            )
        )
    
        return result.scalar_one_or_none()

    async def get_drafts(self):
        result = await self.session.execute(
            select(Video)
            .options(
                selectinload(Video.upload_session),
                selectinload(Video.transcode_task),
            )
            .where(
                Video.publication_status == VideoPublicationStatusEnum.DRAFT
            )
        )
    
        return result.scalars().all()

    async def archive_video(self, id: UUID) -> bool:
        result = await self.session.execute(
            update(Video)
            .where(
                Video.id == id,
                Video.publication_status == VideoPublicationStatusEnum.PUBLISHED
            )
            .values(publication_status=VideoPublicationStatusEnum.ARCHIVED)
        )

        await self.session.flush()
        return result.rowcount > 0

    async def slug_exists(self, slug: str, exclude_video_id: UUID | None = None) -> bool:
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