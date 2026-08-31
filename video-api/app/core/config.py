import os
from typing import List, ClassVar
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

allowed_origins_list: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
    ]

class Settings(BaseSettings):
    app_name: str = "video cms platform"
    env: str = "development"
    debug: bool
    secret_key: str
    database_url: str | None = None  # Not required in production
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    allowed_origins: List[str] = allowed_origins_list
    # docker database envs
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    # r2 creds
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    # buckets
    raw_videos_bucket: str
    processed_videos_bucket: str
    thumbnails_bucket: str
    category_image_bucket: str
    # buckets dev URLs
    raw_videos_bucket_dev_url: str
    thumbnails_bucket_dev_url: str
    category_image_bucket_dev_url: str
    processed_videos_bucket_dev_url: str
    
    model_config = SettingsConfigDict(
        # env_file = ".env",
        #
        # Load env file during development only
        # The production env fie is loaded through the docker compose
        #
        env_file = f".env.{os.getenv('ENV', 'development')}",
        env_file_encoding = "utf-8",
        extra="ignore"
    )

    @property
    def database_url_resolved(self) -> str:
        if self.env == "development":
            if not self.database_url:
                raise ValueError("DATABASE_URL is required in development")
            return self.database_url

        if not all([
            self.postgres_user,
            self.postgres_password,
            self.postgres_db,
            self.postgres_host,
            self.postgres_port,
        ]):
            raise ValueError("All POSTGRES_* variables are required in production")

        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )
    
# The use of @lru_cache() avoids reloading settings every time they are accessed.
@lru_cache()
def get_settings() -> Settings:
    return Settings() # type: ignore  ## type: ignore to suppress warning