from uuid import UUID
import asyncio

from app.repositories.transcode_repository import TranscodeRepository
from app.repositories.video_event_repository import VideoEventRepository
from app.repositories.video_repository import VideoRepository
from app.storage.r2_video_storage import R2VideoStorage
from app.transcoding.transcoder import VideoTranscoder

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

    async def _download_source(self):
        await self.transcode_repository.mark_downloading(...)

        await asyncio.to_thread(
            self.storage.download_source,
            object_key,
            str(video_path),
        )

        await self._record_event(...)

    async def _probe(...):
        await self.transcode_repository.mark_probing(...)

        result = await asyncio.to_thread(
            self.transcoder.probe,
            video_path,
        )

        await self.video_repository.update_metadata(
            video_id,
            ...
        )

        await self._record_event(...)
        
        return result

    async def _transcode(...):
        await self.transcode_repository.mark_transcoding(...)

        result = await asyncio.to_thread(
            self.transcoder.transcode,
            video_path,
            probe_result,
            output_dir,
        )

        await self._record_event(...)

        return result

    async def _upload(...):
        await self.transcode_repository.mark_uploading(...)

        await asyncio.to_thread(
            self.storage.upload_processed,
            output_dir,
            video_path.stem,
        )

        await self._record_event(...)

    # How is it required?
    async def process(
        self, *, task_id: UUID, video_id: UUID, object_key: str,
        upload_id: str, upload_session_id: str, celery_task_id: str, worker_id: str
    ):
        task = await self.transcode_repository.get(task_id)

        if not task:
            raise TranscodeTaskNotFound()

        if task.status == COMPLETED:
            return

        # claim
        await self.transcode_repository.mark_started(...)

        with TemporaryDirectory(prefix="transcode_") as temp:
            video_path = ...
            output_dir = ...

            await self._download(...)
            probe_result = await self._probe(...)
            await self._transcode(...)
            await self._upload(...)
            await self._cleanup_source(...)

            await self._complete(...)