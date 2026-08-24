import uuid
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timezone

from app.core.database import AsyncSession
from app.repositories.upload_repository import UploadRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.video_event_repository import VideoEventRepository
from app.repositories.transcode_repository import TranscodeRepository
from app.repositories.outbox_repository import OutboxMessageRepository

from app.schemas.r2_upload_schema import Part

from app.storage.r2_multipart_service import R2MultipartService

from app.exceptions.upload import NewUploadCreationFailed, UploadSessionNotFound, InvalidUploadState
from app.exceptions.storage import StorageProviderError
from app.exceptions.video import VideoNotFound

from app.models import UploadSessionStatusEnum, VideoProcessingStatusEnum

class UploadService:
    def __init__(
        self,
        session: AsyncSession,
        upload_repository: UploadRepository,
        video_repository: VideoRepository,
        video_event_repository: VideoEventRepository,
        transcode_repository: TranscodeRepository,
        outbox_repository: OutboxMessageRepository,
        storage_service: R2MultipartService,
    ):
        self.session = session
        self.upload_repository = upload_repository
        self.video_repository = video_repository
        self.video_event_repository = video_event_repository
        self.transcode_repository = transcode_repository
        self.outbox_repository = outbox_repository
        self.storage_service = storage_service


    async def new_upload_record(self):
        try:
            # create an empty video and get the video_id
            video = await self.video_repository.create()

            # create a new uploadsession linked to that Video
            upload = await self.upload_repository.create(video_id=video.id)

            # Commit both operations as one transaction
            await self.session.commit()
            await self.session.refresh(video)

            return {
                "success": True,
                "uploadSessionId": str(upload.id),
                "videoId": str(video.id),
            }
        except SQLAlchemyError as exc:
            # The service says: "These three persistence operations constitute one business operation, so rollback everything."
            await self.session.rollback()
            # logger.exception("Failed to create new upload session and new video!")
            raise NewUploadCreationFailed() from exc


    async def initiate(
        self,
        upload_session_id: uuid.UUID,
        video_id: uuid.UUID,
        content_type: str,
        file_name: str,
        file_size_bytes: int,
        total_parts: int
    ):
        upload_id = None
        object_key = str(uuid.uuid4())

        try:
            # 1. Validate video
            video = await self.video_repository.get(video_id)

            if video is None:
                raise VideoNotFound(video_id)

            # 2. Validate upload session belongs to video
            upload_session = await self.upload_repository.get_for_video(
                upload_session_id=upload_session_id,
                video_id=video_id,
            )

            if upload_session is None:
                raise UploadSessionNotFound()

            # 3. Create multipart upload in R2
            response = self.storage_service.create_multipart_upload(
                object_key=object_key,
                content_type=content_type,
            )
            upload_id = response["UploadId"]

            # 4. update_video
            await self.video_repository.update(video_id=video.id, title=file_name)


            # 5. update the upload_session
            await self.upload_repository.update(
                upload_session_id,
                object_key=object_key,
                video_upload_id=upload_id,
                file_size_bytes=file_size_bytes,
                mime_type=content_type,
                original_filename=file_name,
                total_parts=total_parts,
                status=UploadSessionStatusEnum.UPLOADING,
            )

            # 6. Add a video event
            await self.video_event_repository.create_video_event(
                video_id=video_id,
                event_type="UPLOAD_INITIATED",
                payload = {
                    "upload_id": upload_id,
                    "object_key": object_key,
                    "file_name": file_name,
                    "file_size_bytes": file_size_bytes,
                    "content_type": content_type,
                    "total_parts": total_parts,
                    "upload_session_id": str(upload_session_id),
                }
            )

            # 7. Commit DB
            await self.session.commit()

            return {
                "uploadId": upload_id,
                "key": object_key,
            }
        except Exception:
            await self.session.rollback()

            if upload_id is not None:
                try:
                    self.storage_service.abort_multipart_upload(
                        object_key=object_key,
                        upload_id=upload_id,
                    )
                except Exception:
                    # log cleanup failure
                    pass

            raise
        

    async def get_presigned_url(self, *, upload_id: str, object_key: str, part_number: int): #, video_id: uuid.UUID):
        url = self.storage_service.generate_presigned_url(
            object_key=object_key,
            upload_id=upload_id,
            part_number=part_number
        )

        # letting R2StorageService StorageProviderError propagate through.

        # may be this event is not required as it will produce hundreds of entries per video.
        # Create VideoEvent
        # await self.video_event_repository.create_video_event(
        #     video_id = video_id,
        #     event_type="GENERATED_PRESIGNED_URL",
        #     payload={
        #         "upload_id": upload_id,
        #         "object_key": object_key,
        #         "part_number": part_number,
        #     }
        # )

        # await self.session.commit()
        return {"uploadUrl": url}   


    async def complete(self, video_id: uuid.UUID, upload_session_id: uuid.UUID, upload_id: str, object_key: str, parts: list[Part]):
        uploaded_parts = self.storage_service.get_uploaded_parts(
            uploadId=upload_id,
            key=object_key
        )

        if len(uploaded_parts) != len(parts):
            raise ValueError("Mismatch between uploaded parts and client parts")

        # get upload session
        upload_session = await self.upload_repository.get_by_video_and_upload_id(upload_session_id, video_id)

        if upload_session is None:
            raise UploadSessionNotFound() 

        # R2 complete
        self.storage_service.complete_upload(key=object_key, uploadId=upload_id, parts=parts)

        try:
            # Update sesion -> COMPLETED
            await self.upload_repository.update(
                upload_session_id,
                status = UploadSessionStatusEnum.COMPLETED,
                completed_at = datetime.now(timezone.utc),
                uploaded_parts_count = len(uploaded_parts),
            )

            # create a video_event
            await self.video_event_repository.create_video_event(
                video_id=video_id,
                event_type="CHUNKS_UPLOAD_COMPLETED",
                payload={
                    "upload_id": upload_id,
                    "object_key": object_key,
                    "file_name": upload_session.original_filename,
                }
            )

            # Transcode task
            transcode_task = await self.transcode_repository.create(
                video_id=video_id,
                status=VideoProcessingStatusEnum.PENDING
            )

            # Create an OutboxMessage event
            await self.outbox_repository.create(
                event_type="VIDEO_TRANSCODE_REQUESTED",
                aggregate_type="transcode_task",
                aggregate_id=transcode_task.id,
                payload={
                    "object_key": object_key,
                    "video_id": str(video_id),
                    # "upload_id": upload_id,
                    "upload_session_id": str(upload_session_id),
                    "transcode_task_id": str(transcode_task.id),
                },
            )

            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            # # logger.exception(
            #     "Failed to persist completed upload state",
            #     extra={
            #         "video_id": str(video_id),
            #         "upload_session_id": str(upload_session_id),
            #     },
            # )
            try:
                await self.upload_repository.mark_failed(upload_session_id)
                await self.session.commit()
            except SQLAlchemyError:
                await self.session.rollback()
                # logger.exception(
                #     "Failed to mark upload session as FAILED",
                #     extra={
                #         "upload_session_id": str(upload_session_id),
                #     },
                # )
            raise

        return {
            "success": True,
            "status": "upload completed",
            "message": "Upload completed. Processing task will be queued.",
        }
        

    async def pause(self, video_id: uuid.UUID, upload_id: str):
        upload_session = self.upload_repository.get(video_id=video_id)

        if upload_session.status != UploadSessionStatusEnum.UPLOADING:
            # raise HTTPException(status=400, detail="Upload session is not in UPLOADING state")
            raise InvalidUploadState("Upload session is not in UPLOADING state")
        
        try:
            # update upload_session
            await self.upload_repository.update(upload_session.id, status = UploadSessionStatusEnum.PAUSED)

            # create video event
            await self.video_event_repository.create_video_event(
                event_type = "CHUNKS_UPLOAD_PAUSED",
                video_id=video_id,
                payload = {
                    "upload_id": upload_id,
                    "object_key": upload_session.object_key,
                    "file_name": upload_session.original_filename,
                },
            )

            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            # log
            raise

        return { "success": True, "status": "paused"}
        

    async def resume(self, video_id: uuid.UUID, upload_id: str):
        # select upload session
        upload_session = await self.upload_repository.get_by_video(video_id)

        if not upload_session:
            raise UploadSessionNotFound()

        # update upload session
        if upload_session.status != UploadSessionStatusEnum.PAUSED:
            # raise HTTPException(status=400, detail="Upload session is not in PAUSED state")
            raise InvalidUploadState("Upload session is not in PAUSED state")
                    
        # Ask R2 which parts actually exist
        uploaded_parts = self.storage_service.get_uploaded_parts(
            key=upload_session.object_key,
            uploadId=upload_id
        )

        try:
            await self.upload_repository.update(upload_session.id, status = UploadSessionStatusEnum.UPLOADING)

            # Add a VideoEvent to the session
            await self.video_event_repository.create_video_event(
                event_type = "CHUNKS_UPLOAD_RESUMED",
                video_id = video_id,
                payload = {
                    "upload_id": upload_id,
                    "object_key": upload_session.object_key,
                    "file_name": upload_session.original_filename,
                },
            )

            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return {
            "success": True,
            "status": "resumed",
            "uploadId": upload_id,
            "uploaded_parts": uploaded_parts,
        }


    async def abort(self, video_id: uuid.UUID, upload_id: str, object_key: str):
        self.storage_service.abort_multipart_upload(
            object_key=object_key,
            upload_id=upload_id
        )

        # Get upload_session from video_id
        upload_session = await self.upload_repository.get_by_video(video_id=video_id)

        if upload_session is None:
            raise UploadSessionNotFound()

        try:
            # create a video event
            await self.video_event_repository.create_video_event(
                event_type = "CHUNKS_UPLOAD_ABORTED",
                video_id=video_id,
                payload = {
                    "upload_id": upload_id,
                    "object_key": object_key,
                    "file_name": upload_session.original_filename,
                },
            )

            # update upload session
            await self.upload_repository.update(
                upload_session_id=upload_session.id,
                status = UploadSessionStatusEnum.ABORTED,
            )

            await self.session.commit()

        except SQLAlchemyError:
            await self.session.rollback()
            # log
            raise

        return {"success": True, "status": "aborted"}

    
    async def record_uploaded_part(self, video_id: uuid.UUID, upload_id: str, part: Part):
        # select upload session
        upload_session = await self.upload_repository.get_by_video(video_id=video_id)

        if upload_session is None:
            raise UploadSessionNotFound()

        try:
            # create upload part
            await self.upload_repository.create_part(
                upload_session_id=upload_session.id,
                part_number=part.PartNumber,
                etag=part.ETag,
                size_bytes=part.SizeBytes,
            )

            # update upload session
            await self.upload_repository.increment_uploaded_parts(upload_session.id)

            # Add a VideoEvent
            await self.video_event_repository.create_video_event(
                event_type = f"CHUNK_{part.PartNumber}_UPLOADED",
                video_id=video_id,
                payload = {
                    "upload_session_id": str(upload_session.id),
                    "upload_id": upload_id,
                    "partNumber": part.PartNumber,
                    "ETag": part.ETag,
                    "size_bytes": part.SizeBytes,
                }
            )

            await self.session.commit()

        except IntegrityError:
            await self.session.rollback()
            return {
                "success": True,
                "message": "uploaded part already recorded",
            }
        # your service shouldn't know about: HTTPException. That's an HTTP-layer concern.

        except Exception:
            await self.session.rollback()
            raise

        return {
            "success": True,
            "message": "uploaded part recorded successfully"
        }


    async def retry(self, video_id: uuid.UUID):
        upload_session = await self.upload_repository.get_failed_paused_upload(video_id=video_id)
        
        if upload_session is None:
            raise UploadSessionNotFound()
    
        # Ask R2 which parts actually exist
        uploaded_parts = self.storage_service.get_uploaded_parts(
            key=upload_session.object_key,
            uploadId=upload_session.video_upload_id,
        )

        await self.upload_repository.update(status = UploadSessionStatusEnum.UPLOADING)
    
        # Add a VideoEvent
        self.video_event_repository.create_video_event(
            event_type = "CHUNKS_UPLOAD_RETRY",
            video_id=video_id,
            payload = {
                "upload_id": str(upload_session.video_upload_id),
                "object_key": upload_session.object_key,
                "file_name": upload_session.original_filename,
                "upload_session": str(upload_session.id),
                "uploaded_parts": len(uploaded_parts)
            },
        )
            
        await self.session.commit()
    
        return {
            "videoId": video_id,
            "uploadSessionId": str(upload_session.id),
            "uploadId": upload_session.video_upload_id,
            "objectKey": upload_session.object_key,
            "uploaded_parts": uploaded_parts,
        }
    