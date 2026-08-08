from fastapi import HTTPException, Request, Response, Depends, APIRouter, Query, status, Cookie
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi.responses import JSONResponse
from sqlalchemy import select
from datetime import timedelta
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.exc import SQLAlchemyError
import secrets

from app.utils.dependencies import get_db
from app.database.models import User
from app.database.session import AsyncSession
from app.schemas import user_schema, auth_schema
from app.utils import security, jwt_config
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)  # response_model=auth_schema.UserOutWithToken, 
async def register(
    response: Response,
    new_user_data: user_schema.UserCreate,
    session: AsyncSession = Depends(get_db)
):
    # Check if user already exists
    # if db.query(User).filter(User.email == new_user.email).first():
    result = await session.execute(select(User).where(User.email == new_user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered!")

    try:
        new_user = User(
            email = new_user_data.email,
            hashed_password = security.hash_password(new_user_data.password)
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        # Create JWT
        access_token = jwt_config.create_access_token(
            data = {"sub": str(new_user.id)},
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        refresh_token = jwt_config.create_refresh_token(
            data = {"sub": str(new_user.id)},
            expires_delta = timedelta(days=settings.refresh_token_expire_days)
        )
    except (JWTError, SQLAlchemyError, Exception) as e:
        # Delete created user or undo any changes if JWT creation fails
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed, please try again!"
        )
    
    # Send both access and refresh token as cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,              # Set to True in production with HTTPS
        # samesite="strict",        # or 'lax', depending on your frontend/backend separation
        samesite="none",
        path="/"                # Limit access to only the refresh-token route
    )
    
    # samesite="strict", is NOT practical if your frontend and backend are on different subdomains.
    # SameSite=Strict is the most secure if your frontend & backend are on the same origin.
    # SameSite=None is required for true cross-origin cookie usage.
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,              # Set to True in production with HTTPS
        # samesite="strict",        # or 'lax', depending on your frontend/backend separation
        samesite="none",
        path="/"    # Limit access to only the refresh-token route
    )

    # CSRF cookie for added CSRF protection
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be readable by JS
        secure=True,
        # samesite="strict",
        samesite="none",
    )

    # Frontend must send this in a custom header on requests:
    # e.g., X-CSRF-Token: <csrf_token>

    # return {
    #     'message': "New user created successfully!",
    #     'user': new_user,
    #     'token_type': 'bearer',
    #     'access_token': access_token,
    #     'refresh_token': refresh_token,
    #     'csrf_token': csrf_token
    # }


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)  # , response_model=auth_schema.UserLogin
async def login(
    response: Response,
    # form_data: OAuth2PasswordRequestForm = Depends(), # not using form data
    login_data: auth_schema.LoginInput,
    session: AsyncSession = Depends(get_db)
):
    # user = db.query(User).filter(User.email == login_data.email).first()
    result = await session.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials!")
    
    try:
        access_token = jwt_config.create_access_token(
            data = {"sub": str(user.id)},
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        )
        refresh_token = jwt_config.create_refresh_token(
            data = {"sub": str(user.id)},
            expires_delta = timedelta(days=settings.refresh_token_expire_days)
        )
    except (JWTError, Exception) as e:
        raise HTTPException(status_code=500, detail="Login failed, Please try again!")

    # Send both access and refresh token as cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,              # Set to True in production with HTTPS
        # samesite="strict",        # or 'lax', depending on your frontend/backend separation
        samesite="none",
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,              # Set to True in production with HTTPS
        # samesite="strict",        # or 'lax', depending on your frontend/backend separation
        samesite="none",
        path="/" # Limit access to only the refresh-token route. 
                # Though, "api/auth/refresh-token" was making refresh_token undefined in next.js
    )

    # CSRF cookie for added CSRF protection
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be readable by JS
        secure=True,
        # samesite="strict"
        samesite="none"
    )

    # Frontend must send this in a custom header on requests:
    # e.g., X-CSRF-Token: <csrf_token>

    # return {
    #     'message': 'login successful!',
    #     'access_token': access_token,
    #     'refresh_token': refresh_token,
    #     'token_type': 'bearer',
    #     'csrf_token': csrf_token,
    # }


@router.post("/refresh-token", status_code=status.HTTP_204_NO_CONTENT) # response_model=auth_schema.TokenSchema, 
async def refresh_token(response: Response, request: Request, session: AsyncSession = Depends(get_db)):
    # print("COOKIE: ", request.cookies)
    refresh_token_from_cookie = request.cookies.get("refresh_token")
    
    if not refresh_token_from_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    
    try:
        import uuid
        payload = jwt.decode(refresh_token_from_cookie, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token!")

        result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")
        
        access_token = jwt_config.create_access_token(data={"sub": str(user.id)})
        
        # Send a new access token as cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,              # Set to True in production with HTTPS
            # samesite="strict",        # or 'lax', depending on your frontend/backend separation
            samesite="none",
            path="/"     # Limit access to only the refresh-token route
        )
        # return {"access_token": access_token, "token_type": "bearer"}
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid!")
    

@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(key='access_token', httponly=True, secure=True, samesite='none')
    response.delete_cookie(key='refresh_token', httponly=True, secure=True, samesite='none') #, path='/refresh_token')
    response.delete_cookie(key='csrf_token', httponly=False, secure=True, samesite='none')
    # return {"message": "Logout successful! Cookies cleared."}