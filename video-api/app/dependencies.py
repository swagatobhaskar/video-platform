from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator
from fastapi import Request, HTTPException, status, Depends
from jose import JWTError, jwt
import uuid

from app.config import get_settings
from app.database.session import AsyncSessionLocal
from app.database.session import AsyncSession
from app.database.models import User

settings = get_settings()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        

def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(token: str = Depends(get_token_from_cookie), session: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")    # payload.get() can potentially return None
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
    
    user_result = await session.execute(
        select(User)
        .where(User.id == uuid.UUID(user_id))
    )
        
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user


def verify_csrf(request: Request):
    # print("verify_csrf- headers: ", request.headers)
    csrf_cookie = request.cookies.get('csrf_token')
    csrf_header = request.headers.get('X-CSRF-Token')
    # print(f"CSRF HEADER: {csrf_header} | CSRF COOKIE: {csrf_cookie} | [{csrf_header == csrf_cookie}]")
    
    if not csrf_cookie or not csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token not found!")

    if csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token! Value does not match with X-CSRF-Header!"
        )
    