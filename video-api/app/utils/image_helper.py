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


def validate_thumbnail_image(file: UploadFile):

    MAX_SIZE = 5 * 1024 * 1024  # 5 MB

    if file and not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image.")

    # file size
    file.file.seek(0, os.SEEK_END)
    original_size = size_bytes = file.file.tell()
    file.file.seek(0)   # Reset for later reading
    print(size_bytes)

    if original_size > MAX_SIZE:
        raise HTTPException(400, "Image can not be larger than 5MB!")

    if file.content_type not in {
        "image/jpg",
        "image/jpeg",
        "image/png",
    }:
        raise HTTPException(400, "Only JPG, JPEG, and PNG are supported.")

    # read image dimension
    image = Image.open(file.file)
    width, height = image.size
    print(width, height)  # e.g. 1920 1080

    # Converted WebP size
    output = BytesIO()
    image.save(output, format="WEBP", quality=85)
    webp_size = output.tell() # bytes
    output.seek(0)

    print(f"Original: {original_size / 1024:.1f} KB")
    print(f"WebP: {webp_size / 1024:.1f} KB")
    print(f"Dimensions: {image.width}x{image.height}")


def convert_to_webp(file: UploadFile) -> BytesIO:
    image = Image.open(file.file)

    # Preserve alpha channel/transparency for PNGs
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    output = BytesIO()

    # resize before encoding
    image_size = image.size # size returns a tuple: (width, height)
    image.thumbnail((2048, 2048))
    
    image.save(output, format="WEBP", quality=85, method=6)
    output.seek(0)

    return output


# Instead of using pre-signed url this time, the image is uploaded through the backend
async def upload_image_to_r2(image: UploadFile) -> str:
    # extension = image.filename.split(".")[-1]
    extension = Path(image.filename).suffix
    filename = f"{uuid.uuid4()}.{extension}"
    print("Ext, filename: ", extension, filename)

    s3.upload_fileobj(
        image.file,
        settings.category_image_bucket,
        filename,
        ExtraArgs={
            "ContentType": image.content_type,
        },
    )

    # return f"{settings.category_image_bucket_dev_url}/{filename}"
    print("filename after r2 upload: ", filename)
    return filename


async def delete_image_from_r2(object_key: str) -> None:
    await run_in_threadpool(s3.delete_object, Bucket=settings.category_image_bucket, Key=object_key)

async def safe_delete_from_r2(object_key: str) -> None:
    try:
        await delete_image_from_r2(object_key)
    except Exception:
        # Log the error; don't mask the original exception.
        logger.exception("Failed to delete orphaned R2 object: %s", object_key)
