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

    def head_object(self, *, object_key: str):
        return self.client.head_object(Bucket=self.BUCKET, Key=object_key)

    def delete_object(self, *, object_key: str):
        return self.client.delete_object(Bucket=self.BUCKET, Key=object_key)
    