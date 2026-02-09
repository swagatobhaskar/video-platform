1. Create a virtual environment with `python3 -m venv env`, and activate it with `source env/bin/activate`,
2. Install these dependencies: `pip install "fastapi[standard]" sqlalchemy asyncpg python-dotenv psycopg2-binary gunicorn alembic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart`,


## Corrections:
1. Change routes.user_routes `prefix` to `'/api/user'`.
2. 