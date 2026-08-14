from botocore.exceptions import ClientError

from app.exceptions.storage import StorageProviderError
from .base import create_s3_client
from app.core.config import get_settings
settings = get_settings()

BUCKET = settings.raw_videos_bucket

class R2MultipartService:
    def __init__(self, client=None): # client=s3
        self.client = client or create_s3_client

    def create_multipart_upload(self, object_key: str, content_type: str):
        try:
            return self.client.create_multipart_upload(
                Bucket=BUCKET,
                Key=object_key,
                ContentType=content_type,
            )

        except ClientError as exc: # or other s3 exceptions
            # log
            # you don't need to abort if create_multipart_upload() itself failed.
            # NOT REQUIRED:
            # self.abort_multipart_upload(object_key=object_key, bucket=BUCKET, upload_id=response['upload_id'])
            # R2 cleanup belongs in the service workflow
            # you shouldn't pretend R2 + DB are one transaction.
            raise StorageProviderError() from exc

    def generate_presigned_url(self, object_key: str, upload_id: str, part_number: int) -> str:
        try:
            return self.client.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": BUCKET,
                    "Key": object_key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=3600,
            )
        except ClientError as exc:
            raise StorageProviderError(
                "Failed to generate presigned upload URL"
            ) from exc

    def get_uploaded_parts(self, key: str, uploadId: str):
        response = self.client.list_parts(
            Bucket=BUCKET,
            Key=key,
            UploadId=uploadId
        )
        
        return response.get("Parts", [])


    def complete_upload(self, key: str, uploadId: str, parts: dict[str, int]):
        self.client.complete_multipart_upload(
            Bucket=BUCKET,
            Key=key,
            UploadId=uploadId,
            MultipartUpload={
                # "Parts": req.parts,  # [{ETag, PartNumber}]
                "Parts": [
                    {
                        "ETag": part.ETag,
                        "PartNumber": part.PartNumber
                    }
                    for part in parts
                ]
            },
        )

    def abort_multipart_upload(self, object_key: str, upload_id: str):
        self.client.abort_multipart_upload(
            Bucket=BUCKET,
            Key=object_key,
            UploadId=upload_id
        )
