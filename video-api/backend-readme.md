1. Create a virtual environment with `python3 -m venv env`, and activate it with `source env/bin/activate`,
2. Install these dependencies: `pip install "fastapi[standard]" sqlalchemy asyncpg python-dotenv psycopg2-binary gunicorn alembic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart`,


# Alembic Setup
1. Configure alembic.ini
    Set a sync database URL (Alembic itself is sync):
    `sqlalchemy.url = postgresql://user:password@localhost/dbname`

    > Why sync? \
    > Alembic migrations run synchronously \
    > Even though your app is async, migrations are not

2. Configure Alembic for async SQLAlchemy
    Edit `alembic/env.py`
    ```
    import asyncio
    from logging.config import fileConfig

    from sqlalchemy import pool
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import async_engine_from_config

    from alembic import context

    from app.db.base import Base
    from app.db import models  # <-- ensures models are imported

    Set metadata
    target_metadata = Base.metadata
    ```
    **Async migration runner**

    Replace the default run_migrations_online with this:
    ```
    def run_migrations_online() -> None:
        connectable = async_engine_from_config(
            context.config.get_section(context.config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async def run_migrations() -> None:
            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)

        asyncio.run(run_migrations())
    ```

    And define:
    ```
    def do_run_migrations(connection: Connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()
    ```
    **Keep `run_migrations_offline` mostly unchanged.** Offline migrations stay sync and simple.

3. Create your first migration: `alembic revision --autogenerate -m "create users table"`

4. Run migrations: `alembic upgrade head`

