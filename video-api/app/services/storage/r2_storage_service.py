
class R2StorageService:

    def start_multipart_upload(self, bucket: str, key: str, content_type: str):
        return self.client.create_multipart_upload(
            Bucket=bucket,
            Key=key,
            ContentType=content_type,
        )