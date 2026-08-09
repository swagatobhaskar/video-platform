import uuid
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import AsyncSession
from app.repositories.upload_repository import UploadRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.video_event_repository import VideoEventRepository

from app.services.storage.r2_storage_service import R2StorageService

from app.exceptions.upload import NewUploadCreationFailed, UploadServiceError
from app.exceptions.storage import StorageProviderError

class UploadService:
    def __init__(
        self,
        upload_repository: UploadRepository,
        video_repository: VideoRepository,
        video_event_repository: VideoEventRepository,
        session: AsyncSession,
    ):
        self.upload_repository = upload_repository
        self.video_repository = video_repository
        self.video_event_repository = video_event_repository
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


    async def initiate(self, upload_session_id: uuid.UUID, video_id: uuid.UUID, bucket: str, contentType: str, fileName: str, fileSizeBytes: int, totalParts: int):

        upload_id = None
        object_key = None

        object_key = f"{uuid.uuid4()}"
        
        response = R2StorageService.create_multipart_upload(
            bucket=bucket,
            object_key=object_key,
            content_type=contentType,
        )
        upload_id = response["UploadId"]

        video = await self.video_repository.get(video_id)
        # update_video
        self.video_repository.update(video_id=video.id, data=(title=fileName))
        #get the upload_session
        upload_session = await self.upload_repository.update(upload_session_id,
            data= (object_key=object_key,
                   video_upload_id=upload_id,
                   file_size_bytes=req.fileSizeBytes,
                   mime_type=req.contentType,
                    original_filename=req.fileName,
                    total_parts=req.totalParts,
                    status=UploadSessionStatusEnum.UPLOADING,
        ))

        # Add a video event
        self.video_event_repository.create_video_event(
            video_id=video_id,
            event_type="UPLOAD_INITIATED",
            payload = {
                "upload_id": upload_id,
                "object_key": object_key,
                "file_name": fileName,
                "file_size_bytes": fileSizeBytes,
                "content_type": contentType,
                "total_parts": totalParts,
                "upload_session_id": str(upload_session_id),
            }
        )

        try:        
            await self.session.commit()
            await self.session.refresh(upload_session)
        except UploadServiceError():
            if upload_id and object_key:
                await self.session.rollback()

        return {
            "uploadId": upload_id,
            "key": object_key,
        }
        

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
