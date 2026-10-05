from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import AsyncSession
from app.repositories.transcoded_upload_repository import TranscodedUploadRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.video_event_repository import VideoEventRepository

from app.exceptions.video import VideoNotFound
from app.exceptions.upload import (
    UploadSessionNotFound, InvalidUploadState, UploadedFileNotFound,
    NewUploadCreationFailed, UploadAlreadyCompleted
)

from app.schemas.transcoded_upload_schema import TranscodedFileRequest, validate_transcoded_relative_path
from app.models.upload import TranscodedUploadStatusEnum, TranscodedUploadSession, TranscodedUploadFile
from app.storage.r2_transcoded_upload_service import R2TranscodedUploadService

def build_object_key(video_id: UUID, relative_path: str) -> str:
    """
    NOTE:
    Placeholder -- namespaced by video_id so the same relative_path can't
    collide across two different videos. Confirm it matches the layout your
    pipeline actually expects (Video.object_key / dash_manifest_key /
    hls_manifest_key use a *different* UUID set elsewhere at publish time,
    not video_id, so you may want this to line up with that instead).
    """
    return f"{video_id}/{relative_path}"

class TranscodedUploadService:

    def __init__(
        self,
        session: AsyncSession,
        transcoded_upload_repository: TranscodedUploadRepository,
        video_repository: VideoRepository,
        video_event_repository: VideoEventRepository,
        storage_service: R2TranscodedUploadService,
    ):
        self.session = session
        self.transcoded_upload_repository = transcoded_upload_repository
        self.video_repository = video_repository
        self.video_event_repository = video_event_repository
        self.storage_service = storage_service

    async def new_transcoded_upload_record(self):
        try:
            # create an empty video and get the video_id
            video = await self.video_repository.create()

            # create a new uploadsession linked to that Video
            upload = await self.transcoded_upload_repository.create(video_id=video.id)

            # Commit both operations as one transaction
            await self.session.commit()
            await self.session.refresh(video)

            return {
                "success": True,
                "transcodedUploadSessionId": str(upload.id),
                "videoId": str(video.id),
            }
        
        except SQLAlchemyError as exc:
            # The service says: "These three persistence operations constitute one business operation, so rollback everything."
            await self.session.rollback()
            # logger.exception("Failed to create new transcoded upload session and new video!")
            raise NewUploadCreationFailed() from exc


    async def get_batch_presigned_urls(
        self, *, video_id: UUID, upload_session_id: UUID, files: list[TranscodedFileRequest]
    ):
        transcoded_upload_session = await self.transcoded_upload_repository.get_by_video(upload_session_id, video_id)

        if transcoded_upload_session is None:
            raise UploadSessionNotFound()

        if transcoded_upload_session.status not in {
            TranscodedUploadStatusEnum.PENDING,
            TranscodedUploadStatusEnum.UPLOADING,
            TranscodedUploadStatusEnum.PAUSED,
        }:
            raise InvalidUploadState()

        result = []

        for file in files:
            validate_transcoded_relative_path(file.relative_path)

            object_key = build_object_key(video_id, file.relative_path)

            # Create/update database record.
            upload_file = await self.transcoded_upload_repository.get_file_by_path(transcoded_upload_session.id, file.relative_path)

            if upload_file is None:
                upload_file = await self.transcoded_upload_repository.create_file(
                    upload_session_id=transcoded_upload_session.id,
                    client_file_id=file.file_id,
                    relative_path=file.relative_path,
                    object_key=object_key,
                    size_bytes=file.size_bytes,
                    content_type=file.content_type,
                )

            # Already uploaded?
            if upload_file.status == "UPLOADED":
                result.append({
                    "file_id": file.file_id,
                    "object_key": object_key,
                    "already_uploaded": True,
                })
                continue

            upload_url = self.storage_service.generate_presigned_put_url(
                    object_key=object_key,
                    content_type=file.content_type,
                )

            result.append({
                "file_id": file.file_id,
                "object_key": object_key,
                "upload_url": upload_url,
                "already_uploaded": False,
            })

        await self.session.commit()

        return {"files": result}

    async def record_uploaded_file(self, *, video_id: UUID, upload_session_id: UUID, file_id: str):
        upload_file = await self.transcoded_upload_repository.get_file_by_client_id(upload_session_id, file_id)

        if upload_file is None:
            raise UploadedFileNotFound()

        if upload_file.status == "UPLOADED":
            return {
                "success": True,
                "message": "file already recorded",
            }

        # Optional but valuable:
        # verify R2 actually contains the object.
        self.storage_service.head_object(object_key=upload_file.object_key)

        try:
            await self.transcoded_upload_repository.mark_file_uploaded(upload_file.id)
            await self.transcoded_upload_repository.increment_uploaded_files(upload_session_id)
            await self.transcoded_upload_repository.increment_uploaded_bytes(upload_session_id, upload_file.size_bytes)
            await self.video_event_repository.create_video_event(
                video_id=video_id,
                event_type="TRANSCODED_FILE_UPLOADED",
                payload={
                    "upload_session_id": str(upload_session_id),
                    "file_id": file_id,
                    "relative_path": upload_file.relative_path,
                    "object_key": upload_file.object_key,
                    "size_bytes": upload_file.size_bytes,
                },
            )

            await self.session.commit()

        except IntegrityError:
            await self.session.rollback()

            return {
                "success": True,
                "message": "file already recorded",
            }

        return {
            "success": True,
            "message": "file recorded successfully",
        }


    async def pause(self, *, video_id: UUID, upload_session_id: UUID):
        upload = await self.transcoded_upload_repository.get_by_video(upload_session_id, video_id)

        if upload is None:
            raise UploadSessionNotFound()

        if upload.status != TranscodedUploadStatusEnum.UPLOADING:
            raise InvalidUploadState()

        await self.transcoded_upload_repository.update(upload.id, status=TranscodedUploadStatusEnum.PAUSED)
        await self.session.commit()
        return {
            "success": True,
            "status": "paused",
        }

    async def resume(self, *, video_id: UUID, upload_session_id: UUID):
        upload = await self.transcoded_upload_repository.get_by_video(upload_session_id, video_id)

        if upload is None:
            raise UploadSessionNotFound()

        if upload.status != TranscodedUploadStatusEnum.PAUSED:
            raise InvalidUploadState()

        await self.transcoded_upload_repository.update(
            upload.id,
            status=TranscodedUploadStatusEnum.UPLOADING,
        )
        await self.session.commit()
        return {
            "success": True,
            "status": "resumed",
        }


    async def complete(self, *, video_id: UUID, upload_session_id: UUID):
        upload = await self.transcoded_upload_repository.get_by_video(upload_session_id, video_id)

        if upload is None:
            raise UploadSessionNotFound()

        files = await self.transcoded_upload_repository.get_files(upload.id)

        if not files:
            raise InvalidUploadState("No transcoded files were uploaded.")

        incomplete = [file for file in files if file.status != "UPLOADED"]

        if incomplete:
            raise InvalidUploadState(f"{len(incomplete)} files are still pending.")

        # Required files
        paths = {file.relative_path for file in files}
        has_manifest = any(path.endswith("/dash/manifest.mpd") for path in paths)
        has_master = any(path.endswith("/dash/master.m3u8") for path in paths )
        has_segments = any(path.endswith(".m4s") for path in paths)

        if not has_manifest:
            raise InvalidUploadState("manifest.mpd is missing.")

        if not has_master:
            raise InvalidUploadState("master.m3u8 is missing.")

        if not has_segments:
            raise InvalidUploadState("No media segments were uploaded.")

        await self.transcoded_upload_repository.update(
            upload.id,
            status=TranscodedUploadStatusEnum.COMPLETED,
            completed_at=datetime.now(timezone.utc),
        )
        await self.session.commit()
        return {
            "success": True,
            "status": "completed",
        }

    async def abort(self, *, video_id: UUID, upload_session_id: UUID):
        upload = await self.transcoded_upload_repository.get_by_video(upload_session_id, video_id)

        if upload is None:
            raise UploadSessionNotFound()

        if upload.status in {TranscodedUploadStatusEnum.COMPLETED, TranscodedUploadStatusEnum.ABORTED}:
            raise InvalidUploadState()

        files = await self.transcoded_upload_repository.get_files(upload.id)

        for file in files:
            # Best-effort cleanup -- don't let one bad delete block the rest.
            try:
                self.storage_service.delete_object(object_key=file.object_key)
            except Exception:
                pass

        await self.transcoded_upload_repository.update(upload.id, status=TranscodedUploadStatusEnum.ABORTED)
        await self.session.commit()
        return {
            "success": True,
            "status": "aborted",
        }

    async def get_status(self, *, video_id: UUID, upload_session_id: UUID):
        upload = await self.transcoded_upload_repository.get_by_video(upload_session_id, video_id)

        if upload is None:
            raise UploadSessionNotFound()

        return {
            "uploadSessionId": str(upload.id),
            "status": upload.status,
            "totalFiles": upload.total_files,
            "uploadedFiles": upload.uploaded_files,
            "totalBytes": upload.total_bytes,
            "uploadedBytes": upload.uploaded_bytes,
            "createdAt": upload.created_at.isoformat(),
            "completedAt": upload.completed_at.isoformat() if upload.completed_at else None,
        }
    