
class UploadService:
    def __init__(self):
        pass

    async def new_upload(self):
        pass

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

    async def record_part(self, video_id):
        pass
