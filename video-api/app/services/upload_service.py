import uuid
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timezone, UTC
import redis
import kombu

from app.core.database import AsyncSession
from app.repositories.upload_repository import UploadRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.video_event_repository import VideoEventRepository
from app.repositories.transcode_repository import TranscodeRepository

from app.services.storage.r2_storage_service import R2StorageService

from app.exceptions.upload import NewUploadCreationFailed, UploadServiceError
from app.exceptions.storage import StorageProviderError

from app.models import UploadSessionStatusEnum, VideoProcessingStatusEnum

class UploadService:
    def __init__(
        self,
        upload_repository: UploadRepository,
        video_repository: VideoRepository,
        video_event_repository: VideoEventRepository,
        transcode_repository: TranscodeRepository,
        session: AsyncSession,
    ):
        self.upload_repository = upload_repository
        self.video_repository = video_repository
        self.video_event_repository = video_event_repository
        self.transcode_repository = transcode_repository
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
        self.video_repository.update(video_id=video.id, title=fileName)
        # get the upload_session
        upload_session = await self.upload_repository.update(
            upload_session_id,
            object_key=object_key,
            video_upload_id=upload_id,
            file_size_bytes=fileSizeBytes,
            mime_type=contentType,
            original_filename=fileName,
            total_parts=totalParts,
            status=UploadSessionStatusEnum.UPLOADING,
        )

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
        

    async def get_presigned_url(self, bucket: str, video_id: uuid.UUID, upload_id: str, object_key: str, part_number: int):
        url = R2StorageService.generate_presigned_url(
            bucket=bucket,
            object_key=object_key,
            upload_id=upload_id,
            part_number=part_number
        )

        # Create VideoEvent
        self.video_event_repository.create_video_event(
            video_id = video_id,
            event_type="GENERATED_PRESIGNED_URL",
            payload={
                "upload_id": upload_id,
                "object_key": object_key,
                "part_number": part_number,
            }
        )

        await self.session.commit()
        return {"uploadUrl": url}   


    async def complete(self, video_id: uuid.UUID, upload_session_id: uuid.UUID, upload_id: str, bucket: str, object_key: str, parts):
        uploaded_parts = R2StorageService.get_uploaded_parts(
            bucket=bucket,
            uploadId=upload_id,
            key=object_key
        )

        if len(uploaded_parts) != len(parts):
            raise ValueError("Mismatch between uploaded parts and client parts")

        # complete
        R2StorageService.complete_upload(bucket=bucket, key=object_key, uploadId=upload_id, parts=parts)

        # get upload session
        upload_session = self.upload_repository.get(upload_session_id)

        # create a video_event
        self.video_event_repository.create_video_event(
            video_id=video_id,
            event_type="CHUNKS_UPLOAD_COMPLETED",
            payload={
                "upload_id": upload_id,
                "object_key": object_key,
                "file_name": upload_session.original_filename,
            }
        )

        try:
            # Update sesion
            self.upload_repository.update(
                upload_session_id,
                status = UploadSessionStatusEnum.COMPLETED,
                completed_at = datetime.now(timezone.utc),
                uploaded_parts_count = len(uploaded_parts),
            )
        except SQLAlchemyError:
            self.upload_repository.update(status = UploadSessionStatusEnum.FAILED)

        transcode_task = self.transcode_repository.create(
            video_id=video_id,
            status=VideoProcessingStatusEnum.PENDING
        )

        await self.session.commit()

        # Phase 3: Send Task to Redis
        task_id: str | None = None
        try:
            # start celery transcode task
            task = process_video_worker_operations.delay( # type: ignore
                object_key=object_key,
                video_id=video_id,
                upload_id=upload_id,
                upload_session_id=upload_session_id,
                transcode_task_id=str(transcode_task.id),
            )
            
            task_id = str(task.id)

            # update transcode task
            self.transcode_repository.update(status = VideoProcessingStatusEnum.QUEUED)
        except (
                redis.exceptions.ConnectionError,
                kombu.exceptions.OperationalError,
                RuntimeError
            ) as e:
                # update transcode task
                self.transcode_repository.update(status = VideoProcessingStatusEnum.QUEUE_FAILED)
                await self.session.commit()
                
        return {
            "success": True,
            "taskId": task_id if task_id else "Transcoding QUEUE_FAILED",
            "status": "upload completed",
            "message": (
                "Upload completed and processing task queued." if task_id 
                else "Upload completed. Processing is PENDING. \
                    Task will be queued when the service is available."
            ),
        }
        

    async def pause(self, video_id, upload_id):
        pass

    async def resume(self, video_id, upload_id):
        pass

    async def abort(self, video_id, upload_id):
        pass

    async def record_uploaded_part(self, video_id):
        pass
