from io import BytesIO
from botocore.exceptions import ClientError

from app.exceptions.storage import StorageProviderError
from .base import s3

class R2StorageService:
    def __init__(self, client=s3):
        self.client = client

    def create_multipart_upload(self, bucket: str, object_key: str, content_type: str):
        try:
            response = self.client.create_multipart_upload(
                Bucket=bucket,
                Key=object_key,
                ContentType=content_type,
            )

            return response
        except ClientError: # or other s3 exceptions
            # log
            self.abort_multipart_upload(object_key=object_key, bucket=bucket, upload_id=response['upload_id'])
            raise StorageProviderError()

    def generate_presigned_url(self, bucket: str, object_key: str, upload_id: str, part_number: int) -> str:
        url = s3.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket": bucket,
                "Key": object_key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=3600,
        )
        return url


    def get_uploaded_parts(self, bucket: str, key: str, uploadId: str):
        response = self.client.list_parts(
            Bucket=bucket,
            Key=key,
            UploadId=uploadId
        )
        
        return response.get("Parts", [])


    def complete_upload(self, bucket: str, key: str, uploadId: str, parts: dict[str, int]):
        s3.complete_multipart_upload(
            Bucket=bucket,
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

    def abort_multipart_upload(self, bucket: str, object_key: str, upload_id: str):
        self.client.abort_multipart_upload(
            Bucket=bucket,
            Key=object_key,
            UploadId=upload_id
        )


    def upload_thumbnail(self, bucket: str, key: str, img_buffer: BytesIO) -> str:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=img_buffer,
            ContentType="image/webp",
        )
        return key

    def delete_image_from_storage(self, key: str, bucket: str) -> None:
        self.client.delete_object(
            Bucket=bucket,
            Key=key,
        )
