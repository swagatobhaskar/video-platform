from io import BytesIO
from fastapi import HTTPException
from botocore.exceptions import ClientError


class ImageStorage:
    # dependency injection is providing the s3 client where this class is used
    def __init__(self, client=None):
        self.client = client #or get_s3_client()

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
