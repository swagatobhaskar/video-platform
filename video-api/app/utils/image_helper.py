import os
from io import BytesIO
from PIL import Image
from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import uuid
import logging

from .r2_helper import s3
from app.config import get_settings
settings = get_settings()

logger = logging.getLogger(__name__)


"""
⭐️ YouTube video thumbnails should be uploaded at a size of 3840 x 2160 pixels so that they are optimized for TV viewers on YouTube. This is heavily increased from the previous 1280 x 720 limit.
YouTube thumbnails are a aspect ratio of 16:9 (same as widescreen video).
The minimum width of YouTube thumbnails is 640 pixels.
YouTube thumbnail files should be under 50MB.
Supported image formats for thumbnails are JPG, GIF, or PNG.
"""


async def validate_image(file: UploadFile) -> bytes:

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    ALLOWED_TYPES = {
        "image/jpg",
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file and not file.content_type in ALLOWED_TYPES:
        raise HTTPException(400, "Unsupported image type.")

    data = await file.read()

    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image exceeds maximum size.")

    return data

    # file size
    # file.file.seek(0, os.SEEK_END)
    # original_size = size_bytes = file.file.tell()
    # file.file.seek(0)   # Reset for later reading
    # print(size_bytes)

    # read image dimension
    # image = Image.open(file.file)
    # width, height = image.size
    # print(width, height)  # e.g. 1920 1080

    # # Converted WebP size
    # output = BytesIO()
    # image.save(output, format="WEBP", quality=85)
    # webp_size = output.tell() # bytes
    # output.seek(0)

    # print(f"Original: {original_size / 1024:.1f} KB")
    # print(f"WebP: {webp_size / 1024:.1f} KB")
    # print(f"Dimensions: {image.width}x{image.height}")


def convert_to_webp(bytes: bytes, file: UploadFile | None = None) -> BytesIO:
    image = Image.open(file.file)

    # Preserve alpha channel/transparency for PNGs
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    output = BytesIO()

    # resize before encoding
    # image_size = image.size # size returns a tuple: (width, height)
    image.thumbnail((2048, 2048))
    
    image.save(output, format="WEBP", quality=85, method=6)
    output.seek(0)

    return output


# Instead of using pre-signed url this time, the image is uploaded through the backend
# async def upload_image_to_r2(image: UploadFile) -> str:
async def upload_image_to_r2(file_bytes: bytes, filename: str, content_type: str, bucket: str) -> str:
    # extension = image.filename.split(".")[-1]
    extension = filename.split(".")[-1]
    key = f"{uuid.uuid4()}.{extension}"
    print("Ext, filename: ", extension, filename)

    s3.upload_fileobj(
        image.file,
        settings.category_image_bucket,
        filename,
        ExtraArgs={
            "ContentType": image.content_type,
        },
    )

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    return {
        "key": key, # filename
        # "url": f"{settings.thumbnails_bucket_dev_url}/{key}",
    }


async def delete_image_from_r2(object_key: str) -> None:
    await run_in_threadpool(s3.delete_object, Bucket=settings.category_image_bucket, Key=object_key)

async def safe_delete_from_r2(object_key: str) -> None:
    try:
        await delete_image_from_r2(object_key)
    except Exception:
        # Log the error; don't mask the original exception.
        logger.exception("Failed to delete orphaned R2 object: %s", object_key)
