from typing import Annotated
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings, Settings
from app.core.database import engine
# from app.database.models.base import Base

from app.api.routes.user import router as UserRouter
from app.api.routes.auth import router as AuthRouter
from app.api.routes.video_upload import router as VideoUploadRouter
from app.api.routes.video import router as VideoRouter
from app.api.routes.category import router as CategoryRouter
from app.api.routes.series import router as SeriesRouter
from app.api.routes.thumbnail_upload import router as ThumbnailRouter
from app.api.routes._task_routes import router as TaskRouter

from app.api.exception_handlers import (
    upload_not_found_handler,
    upload_already_completed_handler,
)

from app.exceptions.upload import (
    UploadNotFound,
    UploadAlreadyCompleted,
)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic: create DB tables
    print("START-UP")
    # async with engine.begin() as conn:
    #    await conn.run_sync(Base.metadata.create_all)
    
    # Base.metadata.create_all is no longer required
    # as database is now handled by Alembic (external to this code)
    yield   # The app runs during this time
    # Shutdown: do any cleanup here if needed
    await engine.dispose()  # clean up

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    UploadNotFound,
    upload_not_found_handler,
)

app.add_exception_handler(
    UploadAlreadyCompleted,
    upload_already_completed_handler,
)

app.include_router(UserRouter)
app.include_router(AuthRouter)
app.include_router(VideoUploadRouter)
app.include_router(TaskRouter)
app.include_router(VideoRouter)
app.include_router(CategoryRouter)
app.include_router(SeriesRouter)
app.include_router(ThumbnailRouter)

# Use settings as Dependency Injection
@app.get("/")
def read_root(settings: Annotated[Settings, Depends(get_settings)]):
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content= {
            "message": "Hello, World!",
            "App name": settings.app_name,
            "env": settings.env,
            "debug": settings.debug
        }
    )