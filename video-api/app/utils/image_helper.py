import os
from io import BytesIO
from PIL import Image, UnidentifiedImageError
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

ALLOWED_FORMATS = {"JPEG", "WEBP", "PNG"}


def validate_image(file: UploadFile) -> str:
    # Ensure we start reading from the beginning.
    file.file.seek(0)

    try:
        with Image.open(file.file) as image:
            image_format = image.format

            if image_format not in ALLOWED_FORMATS:
                raise HTTPException(status_code=400, detail=f"Unsupported image format: {image_format}")

            # Force Pillow to read the entire image structure.
            # Detects truncated/corrupted images.
            image.verify()

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file")

    except OSError:
        raise HTTPException(status_code=400, detail="Corrupted image file")

    finally:
        # Reset because verify() consumes the image stream.
        file.file.seek(0)

    return image_format

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


def convert_to_webp(img_file: UploadFile | None = None) -> bytes:
    # upload_file.file is already a binary file-like object.
    # Pillow can read directly from it without first converting it to bytes
    # or wrapping it in a BytesIO.

    # open the image in Pillow
    # Image.open() does not immediately decode the entire image; it reads enough
    # data to identify the format and loads pixel data lazily when needed.
    image = Image.open(img_file.file)

    # Convert to a mode that WebP supports while preserving transparency
    # for images that have an alpha channel, e.g., PNG.
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    # Create an empty in-memory binary file.
    # Pillow will write the encoded WebP file bytes into this buffer.
    buffer = BytesIO()

    # Resize while preserving the aspect ratio.
    # The image will not be enlarged if it is already smaller than these dimensions.
    image.thumbnail((1920, 1080))

    # Using Pillow's save method, encode the image as WebP and write the resulting bytes into the in-memory buffer.
    image.save(buffer, format="WEBP", quality=85, method=6)

    # Move the buffer cursor back to the beginning.
    # Writing advanced the cursor to the end of the file; this allows subsequent
    # readers (such as boto3/R2 upload) to read from the start.
    buffer.seek(0)

    # Extract the entire WebP file from memory as raw bytes.
    # These bytes can be passed directly to S3/R2 as the Body parameter.
    return buffer.getvalue()


# Instead of using pre-signed url this time, the image is uploaded through the backend
async def upload_image_to_r2(img_file_bytes: bytes, bucket: str) -> str:
    key = f"{uuid.uuid4()}.webp"
    print("Image key: ", key)

    # s3.put_object() is preferred over s3.upload_fileobj() when the contents are coming as bytes, which is here
    # After conversion, bytes of the WebP file is coming directly, instead of a file-like object
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=img_file_bytes,
        ContentType="image/webp",
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
