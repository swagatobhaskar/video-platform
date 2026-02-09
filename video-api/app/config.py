from typing import List, ClassVar
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

allowed_origins_list: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
    ]


class Settings(BaseSettings):
    app_name: str = "video cms platform api"
    env: str = "development"
    debug: bool = True
    secret_key: str
    database_url: str    
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    allowed_origins: List[str] = allowed_origins_list
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra="ignore"
    )
    
# The use of @lru_cache() avoids reloading settings every time they are accessed.
@lru_cache()
def get_settings() -> Settings:
    return Settings() # type: ignore  ## type: ignore to suppress warning