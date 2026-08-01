from io import BytesIO
from PIL import Image, UnidentifiedImageError, ImageOps, DecompressionBombError
from fastapi import UploadFile, HTTPException
import uuid
import logging

from .r2_helper import s3
from app.config import get_settings
settings = get_settings()

logger = logging.getLogger(__name__)


"""
⭐️ YouTube video thumbnails should be uploaded at a size of 3840 x 2160 pixels so that they are optimized for TV viewers on YouTube.
This is heavily increased from the previous 1280 x 720 limit.
YouTube thumbnails are a aspect ratio of 16:9 (same as widescreen video).
The minimum width of YouTube thumbnails is 640 pixels.
YouTube thumbnail files should be under 50MB.
Supported image formats for thumbnails are JPG, GIF, or PNG.
"""

ALLOWED_FORMATS = {"JPEG", "WEBP", "PNG"}

MAX_SIZE = 5 * 1024 * 1024  # 5 MB

MAX_THUMBNAIL_SIZE = (1920, 1080)

# Decompression-bomb protection: Pillow already has protection for huge images.
# Set pixel dimension limit: A malicious image can be small on disk but huge when decoded.
Image.MAX_IMAGE_PIXELS = 25_000_000 # Set it at the top

# Its return type is None because it either raises exceptions or retruns nothing when passed
def validate_image(file: UploadFile) -> None:
    stream = file.file
    # Ensure we start reading from the beginning.
    stream.seek(0)

    stream.seek(0, 2)  # seek to end
    size_bytes = stream.tell()
    # return to start of file
    stream.seek(0)

    logger.info("Uploaded image size: %.1f KB", size_bytes / 1024)

    if size_bytes > MAX_SIZE:
        raise HTTPException(400, "Image too large")
    
    # MAX_PIXELS = 25_000_000  # ~25 megapixels

    stream.seek(0)

    try:
        with Image.open(stream) as image:
            # if image.width * image.height > MAX_PIXELS:
            #     raise HTTPException(400, "Image dimensions too large")

            if image.format not in ALLOWED_FORMATS:
                raise HTTPException(status_code=400, detail=f"Unsupported image format: {image.format}")

            # Force Pillow to read the entire image structure.
            # Detects truncated/corrupted images.
            # verify() validates the file structure but doesn't fully decode the image.
            image.verify()

        stream.seek(0)
        # This forces a full decode and catches some corrupt images that verify() alone won't.
        with Image.open(stream) as image:
            image.load()

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file")

    except OSError:
        raise HTTPException(status_code=400, detail="Corrupted image file")

    except DecompressionBombError:
        raise HTTPException(status_code=400, detail="Image file is a decompression bomb")

    finally:
        # Reset because verify() consumes the image stream.
        stream.seek(0)


def convert_to_webp(img_file: UploadFile) -> BytesIO:
    # upload_file.file is already a binary file-like object.
    # Pillow can read directly from it without first converting it to bytes
    # or wrapping it in a BytesIO.

    # don't assume the cursor is at the beginning. Start with:
    img_file.file.seek(0)

    # open the image in Pillow
    # Image.open() does not immediately decode the entire image; it reads enough
    # data to identify the format and loads pixel data lazily when needed.
    image = Image.open(img_file.file)

    # Many JPEGs store orientation in EXIF rather than rotating the pixels.
    # If you don't account for it, some uploaded photos may appear sideways after conversion.
    # Before resizing, add:
    image = ImageOps.exif_transpose(image)

    # Convert to a mode that WebP supports while preserving transparency
    # for images that have an alpha channel, e.g., PNG.
    if image.mode in ("RGBA", "LA"):
        pass
    elif "transparency" in image.info:
        image = image.convert("RGBA")
    else:
        image = image.convert("RGB")

    # Create an empty in-memory binary file.
    # Pillow will write the encoded WebP file bytes into this buffer.
    buffer = BytesIO()

    # Resize while preserving the aspect ratio.
    # The image will not be enlarged if it is already smaller than these dimensions.
    image.thumbnail(MAX_THUMBNAIL_SIZE, Image.Resampling.LANCZOS) # (1920, 1080))

    # Using Pillow's save method, encode the image as WebP and write the resulting bytes into the in-memory buffer.
    # Pillow won't automatically preserve EXIF unless requested, so you're already stripping most metadata.
    image.save(buffer, format="WEBP", quality=85, method=6)

    logger.info("Produced WebP size: %d bytes", buffer.tell())

    # Move the buffer cursor back to the beginning.
    # Writing advanced the cursor to the end of the file; this allows subsequent
    # readers (such as boto3/R2 upload) to read from the start.
    buffer.seek(0)

    # Extract the entire WebP file from memory as raw bytes.
    # These bytes can be passed directly to S3/R2 as the Body parameter.
    #return buffer.getvalue()  # returns bytes
    return buffer   # returns BytesIO, boto3.put_object() accepts file-like objects


# Instead of using pre-signed url this time, the image is uploaded through the backend
def upload_image_to_r2(img_buffer: BytesIO, bucket: str) -> str: #dict[str, str]:
    key = f"{uuid.uuid4()}.webp"
    print("Image key: ", key)

    # s3.put_object() is preferred over s3.upload_fileobj() when the contents are coming as bytes, which is here
    # After conversion, bytes of the WebP file is coming directly, instead of a file-like object
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=img_buffer, # img_file_bytes,
        ContentType="image/webp",
    )

    return key

    # return {
    #     "key": key, # filename
    #     "url": f"{settings.thumbnails_bucket_dev_url}/{key}",
    # }


def delete_image_from_r2(key: str, bucket: str) -> None:
    s3.delete_object(
        Bucket=bucket,
        Key=key,
    )
