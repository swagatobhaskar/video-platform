from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings

settings = get_settings()

DEV_DATABASE_URL = settings.database_url if settings.env == "development" else None

PROD_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"{settings.postgres_host}:{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

ENV = settings.env
DATABASE_URL = DEV_DATABASE_URL if ENV == "development" else PROD_DATABASE_URL

print(f"Using DATABASE_URL: {DATABASE_URL}")

engine = create_async_engine(
    url=DATABASE_URL,
    echo=(settings.env == "development"),
    # echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
