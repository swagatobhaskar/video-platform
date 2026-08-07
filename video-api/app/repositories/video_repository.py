from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, joinedload

from app.database.session import AsyncSession
from app.database.models import (
    Video, VideoPublicationStatusEnum, UploadSession,
    UploadSessionStatusEnum, VideoEvent,
)

class VideoRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # pagination later
    async def list(self) -> list[Video]:
        result = await self.session.execute(select(Video))
        return result.scalars().all()
    

    async def get(self, video_id: UUID) -> Video | None:
        result = await self.session.execute(
            select(Video).where(Video.id == video_id)
        )
        return result.scalar_one_or_none()

    
    async def create_video(
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
        self.session.flush(video)
        return video

    """
    Why flush() instead of commit()?
    If create_video() commits...
    ...and create_upload_session() commits...
    ...and create_event() commits...
    ...you've lost the ability to roll everything back as one unit.
    The service should own the transaction.
    """

    async def delete(self, video: Video) -> None:
        await self.session.delete(video)


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


    async def get_full(self, video_id: UUID):
        result = await self.session.execute(
            select(Video)
            .options(
                selectinload(Video.upload_session),
                selectinload(Video.transcode_task),
            )
            .where(Video.id == video_id)
        )
        return result.scalar_one_or_none()

    async def get_with_events(video_id: UUID):
        pass

    async def get_for_player(video_id: UUID):
        pass

    async def get_for_admin(video_id: UUID):
        pass

    # Instead of this dedicated service, do:
    # video = await repo.get(id)
    # status = video.publication_status
    #
    # async def get_publication_status(self, video_id: UUID) -> VideoPublicationStatusEnum | None:
    #     result = await self.session.execute(
    #         select(Video).where(Video.id == video_id)
    #     )
    #     video = result.scalar_one_or_none()
    #     return video.publication_status


    # async def update_publication_status(self, video_id: UUID, new_status: VideoPublicationStatusEnum) -> Video:
    #     result = await self.session.execute(
    #         update(Video).where(Video.id == video_id).values(publication_status = new_status)
    #     )
    #     await self.session.commit()
    #     await self.session.refresh()
    #     return video
    """
    instead do:
    video = await repo.get(video_id)
    video.publication_status = new_status
    Then later:
    await session.commit()
    SQLAlchemy will update automatically.
    """

    # NOT HERE
    # async def find_upload_session(self, video_id: UUID) -> UploadSession:
    #     result = await self.session.execute(
    #         select(Video).where(Video.id == video_id)
    #     )
    #     video = result.scalar_one_or_none()

    #     return video.upload_session

    # NOT HERE
    # async def create_event(self, **data) -> VideoEvent:
    #     video_event = VideoEvent(**data)
    #     await self.session.add(video_event)
    #     await self.session.commit()
    #     await self.session.refresh(video_event)
    #     return video_event