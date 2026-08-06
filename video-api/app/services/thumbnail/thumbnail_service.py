
class ThumbnailService:

    async def upload_thumbnail():

        validate_image()

        convert()

        storage.upload_image()

        save_database()

        create_event()


"""
Your route becomes

@router.post(...)
async def upload(...):
    return await thumbnail_service.upload_thumbnail(...)
"""