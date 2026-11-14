from botocore.exceptions import ClientError

from app.core.config import get_settings
settings = get_settings()


class R2TranscodedUploadService:

    BUCKET = settings.processed_videos_bucket

    def __init__(self, client):
        self.client = client

    def generate_presigned_put_url(self, *, object_key: str, content_type: str) -> str:

        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.BUCKET,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )

    def head_object(self, *, object_key: str) -> int | None:
        """Return the object's size in bytes, or None if it doesn't exist."""
        try:
            resp = self.client.head_object(Bucket=self.BUCKET, Key=object_key)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
        return resp["ContentLength"]

    def delete_object(self, *, object_key: str):
        return self.client.delete_object(Bucket=self.BUCKET, Key=object_key)
    