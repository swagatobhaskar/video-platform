from typing import Annotated
from fastapi import FastAPI, APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings, Settings
from app.database.session import engine, Base

from app.routes.user import router as UserRouter
from app.routes.auth import router as AuthRouter
from app.routes.upload import router as UploadRouter

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

app.include_router(UserRouter)
app.include_router(AuthRouter)
app.include_router(UploadRouter)

router = APIRouter()

# Use settings as Dependency Injection
@app.get("/")
def root_info(settings: Annotated[Settings, Depends(get_settings)]):
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content= {
            "message": "Hello, World!",
            "App name": settings.app_name,
            "env": settings.env,
            "debug": settings.debug
        }
    )