from botocore.exceptions import ClientError
from pathlib import Path

from app.exceptions.storage import StorageProviderError
from .base import create_s3_client
from app.core.config import get_settings

settings = get_settings()

class R2VideoStorage:
    BUCKET = settings.processed_videos_bucket

    def __init__(self, client=None):
        self.client = client or create_s3_client()

    def download_source(self, object_key: str, destination: str) -> None:
        return self.client.download_file(
            settings.raw_videos_bucket,
            object_key,
            destination
        )

    def upload_processed(self, local_dir: Path, object_key: str) -> None:
        BUCKET = settings.processed_videos_bucket
                
        local_dir = Path(local_dir)
        remote_prefix = Path(object_key).stem
        
        failed = []
        
        for file_path in local_dir.rglob("*"):
            if not file_path.is_file():
                continue
        
            key = f"{remote_prefix}/{file_path.relative_to(local_dir)}".replace("\\", "/")
        
            try:
                self.client.upload_file(str(file_path), BUCKET, key)
        
            except Exception as e:
                failed.append(
                    {
                        "file": str(file_path),
                        "key": key,
                        "error": str(e),
                    }
                )
        
        return failed

    def delete_source(self, object_key: str) -> None:
        self.client.delete_object(
            Bucket=settings.raw_videos_bucket,
            Key=object_key,
        )

    def delete_video(self, object_key: str) -> int:
        prefix = f"{object_key}/dash/"

        deleted_count = 0
        continuation_token = None

        try:
            while True:
                params = {
                    "Bucket": self.BUCKET,
                    "Prefix": prefix,
                }

                if continuation_token:
                    params["continuation_token"] = continuation_token

                response = self.client.list_objects_v2(**params)

                objects = response.get("Contents", [])

                if objects:
                    delete_response = self.client.delete_objects(
                        Bucket=self.BUCKET,
                        Delete={
                            "Objects": [{"Key": obj["Key"]} for obj in objects],
                            "Quiet": True,
                        },
                    )

                    errors = delete_response.get("Errors", [])

                    if errors:
                        raise StorageProviderError(f"Failed to delete some R2 objects: {errors}")

                    deleted_count += len(objects)

                if not response.get("IsTruncated"):
                    break

                continuation_token = response["NextContinuationtoken"]

            return deleted_count

        except ClientError as exc:
            raise StorageProviderError("Failed to delete video files from R2") from exc
