
class R2TranscodedUploadService:

    def __init__(self, client, bucket: str):
        self.client = client
        self.bucket = bucket

    def generate_presigned_put_url(
        self,
        *,
        object_key: str,
        content_type: str,
    ) -> str:

        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )

    def head_object(self, *, object_key: str):
        return self.client.head_object(Bucket=self.bucket, Key=object_key)

    def delete_object(self, *, object_key: str):
        return self.client.delete_object(Bucket=self.bucket, Key=object_key)
    