import os
from typing import List, ClassVar
from functools import lru_cache
from sqlalchemy.engine import URL
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
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    allowed_origins: List[str] = allowed_origins_list

    # docker database envs
    database_url: str

    # These are for PostgreSQL container configuration
    # Not required here, in the FastAPI app
    # 
    # postgres_user: str
    # postgres_password: str
    # postgres_db: str
    # postgres_host: str
    # postgres_port: int = 5432

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

    redis_url: str
    
    model_config = SettingsConfigDict(
        # env_file = ".env",
        #
        # Load env file during development only
        # The production env fie is loaded through the docker compose
        #
        # env_file = f".env.{os.getenv('ENV', 'development')}",
        # env_file_encoding = "utf-8",
        extra="ignore"
    )

    # @property
    # def database_url(self) -> str:
    #     return URL.create(
    #         drivername="postgresql+asyncpg",
    #         username=self.postgres_user,
    #         password=self.postgres_password,
    #         host=self.postgres_host,
    #         port=self.postgres_port,
    #         database=self.postgres_db,
    #     ).render_as_string(hide_password=False)
    
# The use of @lru_cache() avoids reloading settings every time they are accessed.
@lru_cache()
def get_settings() -> Settings:
    return Settings() # type: ignore  ## type: ignore to suppress warning