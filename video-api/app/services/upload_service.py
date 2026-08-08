from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import AsyncSession
from app.repositories.upload_repository import UploadRepository
from app.repositories.video_repository import VideoRepository

from app.exceptions.upload import NewUploadCreationFailed

class UploadService:
    def __init__(
        self,
        upload_repository: UploadRepository,
        video_repository: VideoRepository,
        session: AsyncSession,
    ):
        self.upload_repository = upload_repository
        self.video_repository = video_repository
        self.session = session


    async def new_upload_record(self):
        try:
            # create an empty video and get the video_id
            video = await self.video_repository.create()

            # create a new uploadsession linked to that Video
            upload = await self.upload_repository.create(video_id=video.id)

            # Commit both operations as one transaction
            await self.session.commit()

            return {
                "success": True,
                "uploadSessionId": str(upload.id),
                "videoId": str(video.id),
            }
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise NewUploadCreationFailed() from exc    # from exc preserves the original exception as the cause.

    async def initiate(self, video_id):
        # video = await repo.get_video(video_id)
        # upload_session = await repo.get_upload_session(...)
        # object_key = ...
        # storage.start_upload()
        # await repo.mark_upload_started(...)
        # repository.save()
        # create_event()
        # return ...
        pass

    async def get_presigned_url(self, video_id, upload_id):
        pass

    async def pause(self, video_id, upload_id):
        pass

    async def resume(self, video_id, upload_id):
        pass

    async def abort(self, video_id, upload_id):
        pass

    async def complete(self, video_id, upload_id):
        pass

    async def record_uploaded_part(self, video_id):
        pass
