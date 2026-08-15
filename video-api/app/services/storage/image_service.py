from io import BytesIO
from fastapi import UploadFile, HTTPException, Depends
from PIL import Image, ImageOps, UnidentifiedImageError
from botocore.exceptions import ClientError

from .base import create_s3_client
from app.dependencies import get_s3_client


class ImageError(Exception):
    pass


class ImageTooLargeError(ImageError):
    pass


class UnsupportedImageFormatError(ImageError):
    pass


class InvalidImageError(ImageError):
    pass


class CorruptedImageError(ImageError):
    pass

class ImageProcessor:

    ALLOWED_FORMATS = {"JPEG", "WEBP", "PNG"}

    MAX_SIZE = 5 * 1024 * 1024  # 5 MB

    MAX_THUMBNAIL_SIZE = (1920, 1080)

    # Decompression-bomb protection: Pillow already has protection for huge images.
    # Set pixel dimension limit: A malicious image can be small on disk but huge when decoded.
    Image.MAX_IMAGE_PIXELS = 25_000_000 # Set it at the top

    # def __init__(self, client=s3):
    #     self.client = client


    def validate_image(self, file: UploadFile) -> None:
        stream = file.file

        # Measure file size.
        # Ensure we start reading from the beginning.
        stream.seek(0)

        stream.seek(0, 2)  # seek to end
        size_bytes = stream.tell()
        # return to start of file
        stream.seek(0)

        # logger.info("Uploaded image size: %.1f KB", size_bytes / 1024)

        if size_bytes > self.MAX_SIZE:
            # raise HTTPException(400, "Image too large")
            raise ImageTooLargeError("Image too large")
        
        # MAX_PIXELS = 25_000_000  # ~25 megapixels
        # stream.seek(0)

        try:
            with Image.open(stream) as image:
                # if image.width * image.height > MAX_PIXELS:
                #     raise HTTPException(400, "Image dimensions too large")

                if image.format not in self.ALLOWED_FORMATS:
                    # raise HTTPException(status_code=400, detail=f"Unsupported image format: {image.format}")
                    raise UnsupportedImageFormatError(f"Unsupported image format: {image.format}")

                # Force Pillow to read the entire image structure.
                # Detects truncated/corrupted images.
                # verify() validates the file structure but doesn't fully decode the image.
                # verify() intentionally leaves the image unusable.
                image.verify()

            # verify() leaves the stream at EOF.
            stream.seek(0)

            # This forces a full decode and catches some corrupt images that verify() alone won't.
            with Image.open(stream) as image:
                image.load()

        except UnidentifiedImageError:
            # raise HTTPException(status_code=400, detail="Invalid image file")
            raise InvalidImageError("Invalid image file")

        except OSError:
            # raise HTTPException(status_code=400, detail="Corrupted image file")
            raise CorruptedImageError("Corrupted image file")

        # except DecompressionBombError:
        #     raise HTTPException(status_code=400, detail="Image file is a decompression bomb")
        except Image.DecompressionBombError:
            raise InvalidImageError("Image dimensions are too large")

        finally:
            # Reset because verify() consumes the image stream.
            stream.seek(0)


    def create_webp(self, img_file: UploadFile) -> BytesIO:
        # upload_file.file is already a binary file-like object.
        # Pillow can read directly from it without first converting it to bytes
        # or wrapping it in a BytesIO.

        # don't assume the cursor is at the beginning. Start with:
        img_file.file.seek(0)

        # open the image in Pillow
        # Image.open() does not immediately decode the entire image; it reads enough
        # data to identify the format and loads pixel data lazily when needed.
        
        # image = Image.open(img_file.file)
        # using context manager
        with Image.open(img_file.file) as image:

            # Many JPEGs store orientation in EXIF rather than rotating the pixels.
            # If you don't account for it, some uploaded photos may appear sideways after conversion.
            # Before resizing, add:
            image = ImageOps.exif_transpose(image)


            has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
            
            image = image.convert("RGBA" if has_alpha else "RGB")


            # This preserves aspect ratio and crops the excess.
            # image = ImageOps.fit(
            #     image,
            #     (1920, 1080),
            #     method=Image.Resampling.LANCZOS,
            #     centering=(0.5, 0.5),
            # )

            # do not convert if image is already WebP, and it's correctly sized
            # directly return th file-like object
            if (image.format == "WEBP" and image.width <= self.MAX_THUMBNAIL_SIZE[0]
                and image.height <= self.MAX_THUMBNAIL_SIZE[1]
            ):
                img_file.file.seek(0)
                return BytesIO(img_file.file.read())

            # Convert to a mode that WebP supports while preserving transparency
            # for images that have an alpha channel, e.g., PNG.
            # if image.mode in ("RGBA", "LA"):
            #     pass
            # elif "transparency" in image.info:
            #     image = image.convert("RGBA")
            # else:
            #     image = image.convert("RGB")


            # Resize while preserving the aspect ratio.
            # The image will not be enlarged if it is already smaller than these dimensions.
            image.thumbnail(self.MAX_THUMBNAIL_SIZE, Image.Resampling.LANCZOS) # (1920, 1080))

            # Create an empty in-memory binary file.
            # Pillow will write the encoded WebP file bytes into this buffer.
            buffer = BytesIO()

            # Using Pillow's save method, encode the image as WebP and write the resulting bytes into the in-memory buffer.
            # Pillow won't automatically preserve EXIF unless requested, so you're already stripping most metadata.
            image.save(buffer, format="WEBP", quality=85, method=6)

        # logger.info("Produced WebP size: %d bytes", buffer.tell())

        # Move the buffer cursor back to the beginning.
        # Writing advanced the cursor to the end of the file; this allows subsequent
        # readers (such as boto3/R2 upload) to read from the start.
        buffer.seek(0)

        # Extract the entire WebP file from memory as raw bytes.
        # These bytes can be passed directly to S3/R2 as the Body parameter.
        #return buffer.getvalue()  # returns bytes
        return buffer   # returns BytesIO, boto3.put_object() accepts file-like objects


class ImageStorage:
    # dependency injection is providing the s3 client where this class is used
    def __init__(self, client):
        self.client = client

    def upload(self, key: str, bucket: str, img_buffer: BytesIO) -> str:
        img_buffer.seek(0)

        try:
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=img_buffer,
                ContentType="image/webp",
            )
            return key
        except ClientError:
            # logger.exception("Failed to upload image")
            raise HTTPException(503, "Image upload failed")
    

    def delete(self, key: str, bucket: str) -> None:
        try:
            self.client.delete_object(
                Bucket=bucket,
                Key=key,
            )
        except ClientError:
            # logger.exception("Failed to delete orphaned category image from R2: %s", image_key)
            raise # raise what?
