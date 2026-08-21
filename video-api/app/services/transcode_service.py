from uuid import UUID
import asyncio
from datetime import datetime, UTC
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from app.exceptions.transcodetask import TranscodeTaskNotFound
from app.repositories.transcode_repository import TranscodeRepository
from app.repositories.video_event_repository import VideoEventRepository
from app.repositories.video_repository import VideoRepository
from app.storage.r2_video_storage import R2VideoStorage
from app.transcoding.transcoder import VideoTranscoder


# First: The service owns the workflow.
# Second: The service does not know about Celery.
# It receives: progress_callback
# That keeps your service usable outside Celery.

ProgressCallback = Callable[[str, int], None]

class TranscodeService:

    def __init__(
        self,
        transcode_repository: TranscodeRepository,
        video_repository: VideoRepository,
        video_event_repository: VideoEventRepository,
        storage: R2VideoStorage,
        transcoder: VideoTranscoder,
    ):
        self.transcode_repository = transcode_repository
        self.video_repository = video_repository
        self.video_event_repository = video_event_repository
        self.storage = storage
        self.transcoder = transcoder

    async def process(
        self, *, task_id: UUID, video_id: UUID, object_key: str,
        upload_id: str, upload_session_id: str, celery_task_id: str, worker_id: str,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        
        task = await self.transcode_repository.get(task_id)

        if task is None:
            raise TranscodeTaskNotFound(f"TranscodeTask {task_id} not found")

        # Important:
        # claim() is atomic.
        claimed = await self.transcode_repository.claim(
            task_id=task_id,
            celery_task_id=celery_task_id,
            worker_id=worker_id,
        )

        if not claimed:
            # Another Celery delivery is already processing
            # this TranscodeTask, or it has already completed.
            return

        try:
            with TemporaryDirectory(prefix="transcode_") as temp_dir:
                temp_dir = Path(temp_dir)
                video_path = (temp_dir / Path(object_key).name)
                output_dir = (temp_dir / "processed" / video_path.stem)
                output_dir.mkdir(parents=True, exist_ok=True)

                # -------------------------------------------------
                # 1. DOWNLOAD
                # -------------------------------------------------
                self._update_celery_state(progress_callback, "DOWNLOADING", 10)

                await self._download_source(
                    task_id=task_id,
                    video_id=video_id,
                    object_key=object_key,
                    upload_id=upload_id,
                    upload_session_id=upload_session_id,
                    worker_id=worker_id,
                    celery_task_id=celery_task_id,
                    video_path=video_path,
                )

                # -------------------------------------------------
                # 2. PROBE
                # -------------------------------------------------
                self._update_celery_state(progress_callback, "PROBING", 30)

                probe_result = await self._probe(
                    task_id=task_id,
                    video_id=video_id,
                    object_key=object_key,
                    upload_id=upload_id,
                    upload_session_id=upload_session_id,
                    worker_id=worker_id,
                    celery_task_id=celery_task_id,
                    video_path=video_path,
                )

                # -------------------------------------------------
                # 3. TRANSCODE
                # -------------------------------------------------
                self._update_celery_state(progress_callback, "TRANSCODING", 50)

                transcode_result = await self._transcode(
                    task_id=task_id,
                    video_id=video_id,
                    object_key=object_key,
                    upload_id=upload_id,
                    upload_session_id=upload_session_id,
                    worker_id=worker_id,
                    celery_task_id=celery_task_id,
                    video_path=video_path,
                    probe_result=probe_result,
                    output_dir=output_dir,
                )

                # -------------------------------------------------
                # 4. UPLOAD
                # -------------------------------------------------

                self._update_celery_state(progress_callback, "UPLOADING", 70)

                await self._upload(
                    task_id=task_id,
                    video_id=video_id,
                    object_key=object_key,
                    upload_id=upload_id,
                    upload_session_id=upload_session_id,
                    worker_id=worker_id,
                    celery_task_id=celery_task_id,
                    output_dir=output_dir,
                    transcode_result=transcode_result,
                )

                # -------------------------------------------------
                # 5. ASSIGN OBJECT KEY
                # -------------------------------------------------
                await self.video_repository.update(video_id, object_key=object_key)

                await self._record_event(
                    video_id=video_id,
                    transcode_task_id=task_id,
                    event_type="OBJECT_KEY_ASSIGNED_TO_VIDEO",
                    payload={
                        "upload_id": upload_id,
                        "upload_session_id": upload_session_id,
                        "object_key": object_key,
                        "uploaded_file_name": object_key,
                        "worker_id": worker_id,
                        "task_id": celery_task_id,
                    },
                )

                # -------------------------------------------------
                # 6. CLEANUP SOURCE
                # -------------------------------------------------
                self._update_celery_state(progress_callback, "SOURCE_CLEANUP", 90)

                await self._cleanup_source(
                    task_id=task_id,
                    video_id=video_id,
                    object_key=object_key,
                    upload_id=upload_id,
                    upload_session_id=upload_session_id,
                    worker_id=worker_id,
                    celery_task_id=celery_task_id,
                )

                # -------------------------------------------------
                # 7. COMPLETE
                # -------------------------------------------------

                await self.transcode_repository.mark_completed(task_id)

                await self._record_event(
                    video_id=video_id,
                    transcode_task_id=task_id,
                    event_type="PROCESSING_COMPLETED",
                    payload={
                        "upload_id": upload_id,
                        "upload_session_id": upload_session_id,
                        "object_key": object_key,
                        "worker_id": worker_id,
                        "task_id": celery_task_id,
                    },
                )

                self._update_celery_state(progress_callback, "SUCCESS", 100)

        except Exception as exc:
            await self.transcode_repository.mark_failed(task_id, error=str(exc))
            raise

    # =============================================================
    # PHASES
    # =============================================================
    async def _download_source(
        self, *, task_id, video_id, object_key, upload_id,
        upload_session_id, worker_id, celery_task_id, video_path
    ):
        await self.transcode_repository.mark_downloading(task_id, progress=10)

        await self._record_event(
            video_id=video_id,
            transcode_task_id=task_id,
            event_type="SOURCE_VIDEO_DOWNLOAD_STARTED",
            payload={
                "upload_id": upload_id,
                "upload_session_id": upload_session_id,
                "object_key": object_key,
                "worker_id": worker_id,
                "task_id": celery_task_id,
            },
        )

        await asyncio.to_thread(
            self.storage.download_source,
            object_key,
            str(video_path),
        )


    async def _probe(
        self, *, task_id, video_id, object_key, upload_id,
        upload_session_id, worker_id, celery_task_id, video_path,
    ) -> dict:
        await self.transcode_repository.mark_probing(task_id, progress=30)

        probe_result = await asyncio.to_thread(
            self.transcoder.probe,
            video_path,
        )

        video = await self.video_repository.update_technical_metadata(
            video_id,
            fps=probe_result["fps"],
            width=probe_result["width"],
            height=probe_result["height"],
            codec=probe_result["codec"],
            bitrate=probe_result["bitrate"],
            duration_seconds=probe_result["duration"],
        )

        if video is None:
            raise RuntimeError(f"Video {video_id} not found")

        await self._record_event(
            video_id=video_id,
            transcode_task_id=task_id,
            event_type="FFPROBE_COMPLETED",
            payload={
                "upload_id": upload_id,
                "upload_session_id": upload_session_id,
                "object_key": object_key,
                "worker_id": worker_id,
                "task_id": celery_task_id,
                "probe_result": probe_result,
            },
        )

        return probe_result

    async def _transcode(
        self, *, task_id, video_id, object_key, upload_id, upload_session_id,
        worker_id, celery_task_id, video_path, probe_result, output_dir,
    ) -> dict:
        await self.transcode_repository.mark_transcoding(task_id, progress=50)

        result = await asyncio.to_thread(
            self.transcoder.transcode,
            video_path,
            probe_result,
            output_dir,
        )

        await self._record_event(
            video_id=video_id,
            transcode_task_id=task_id,
            event_type="FFMPEG_TRANSCODE_COMPLETED",
            payload={
                "upload_id": upload_id,
                "upload_session_id": upload_session_id,
                "object_key": object_key,
                "worker_id": worker_id,
                "task_id": celery_task_id,
                "transcode_result": result,
            },
        )

        return result


    async def _upload(
        self, *, task_id, video_id, object_key, upload_id, upload_session_id,
        worker_id, celery_task_id, output_dir, transcode_result
    ):
        await self.transcode_repository.mark_uploading(task_id, progress=70)

        await asyncio.to_thread(
            self.storage.upload_processed,
            output_dir,
            object_key,
        )

        await self._record_event(
            video_id=video_id,
            transcode_task_id=task_id,
            event_type="OUTPUT_SEGMENTS_UPLOADED",
            payload={
                "upload_id": upload_id,
                "upload_session_id": upload_session_id,
                "object_key": object_key,
                "worker_id": worker_id,
                "task_id": celery_task_id,
                "transcode_result": transcode_result,
            },
        )

    async def cleanup_source(
        self, *, task_id, video_id, object_key, upload_id,
        upload_session_id, worker_id, celery_task_id
    ):
        await self.transcode_repository.mark_cleanup(task_id, progress=90)

        try:
            await asyncio.to_thread(
                self.storage.delete_source,
                object_key,
            )

        except Exception as exc:

            # Important:
            # transcoding itself succeeded.
            # Source deletion is cleanup and shouldn't cause
            # the whole video to be transcoded again.

            await self._record_event(
                video_id=video_id,
                transcode_task_id=task_id,
                event_type="ORIGINAL_VIDEO_DELETE_FAILED",
                payload={
                    "upload_id": upload_id,
                    "upload_session_id": upload_session_id,
                    "object_key": object_key,
                    "worker_id": worker_id,
                    "task_id": celery_task_id,
                    "error": str(exc),
                },
            )

            return

        await self._record_event(
            video_id=video_id,
            transcode_task_id=task_id,
            event_type="ORIGINAL_VIDEO_DELETED",
            payload={
                "upload_id": upload_id,
                "upload_session_id": upload_session_id,
                "object_key": object_key,
                "worker_id": worker_id,
                "task_id": celery_task_id,
            },
        )

    # =============================================================
    # EVENTS
    # =============================================================
    async def _record_event(
        self, *, video_id: UUID, transcode_task_id: UUID,
        event_type: str, payload: dict,
    ):
        await self.video_event_repository.create_video_event(
            video_id=video_id,
            transcode_task_id=transcode_task_id,
            event_type=event_type,
            payload=payload,
        )

        await self.transcode_repository.session.commit()

    # =============================================================
    # CELERY STATE
    # =============================================================

    @staticmethod
    def _update_celery_state(callback, state: str, progress: int):

        if callback:
            callback(state, progress)
