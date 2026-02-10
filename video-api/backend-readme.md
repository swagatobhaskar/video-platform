1. Create a virtual environment with `python3 -m venv env`, and activate it with `source env/bin/activate`,
2. Install these dependencies: `pip install "fastapi[standard]" sqlalchemy asyncpg python-dotenv psycopg2-binary gunicorn alembic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart`,

# PostgreSQL Container
1. Start a PostgreSQL container directly with the official Docker image:
    ```
    docker run --name video_postgres \
     -e POSTGRES_USER=swagato \
     -e POSTGRES_PASSWORD=^dogesh39A \
     -e POSTGRES_DB=videodevdb \
     -p 5432:5432 \
     -v pgdata:/var/lib/postgresql \
     -d postgres:18
    ```
    * If a postgresql service is already running on port 5432:
      * Find it with: `sudo lsof -i :5432`
      * Stop it with: `sudo service postgresql stop`
      * If you get error like: `docker: Error response from daemon: Conflict. The container name "/video_postgres" is already in use by container`, remove the exisitng container with `docker rm video_postgres`, and re-run the container.

2. Get inside the running container with: `docker exec -it chat_postgres psql -U swagato -d videodevdb`.
    * If you see error like: `Error response from daemon: container 94c21aeab73.. is not running`, check Docker logs with `docker logs video_postgres`.
  
3. Connect to the running PostgreSQL container from your FastAPI app, use the following DATABASE_URL string: `postgresql+asyncpg://swagato:^dogesh39A@localhost:5432/videodevdb`.

