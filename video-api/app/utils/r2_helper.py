import boto3

from app.config import get_settings
settings = get_settings()

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    region_name="auto"
)
