from functools import lru_cache

from .base import create_s3_client


@lru_cache
def get_s3_client():
    return create_s3_client()
