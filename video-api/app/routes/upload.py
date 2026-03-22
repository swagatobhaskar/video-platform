import os
import shutil
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post('/video')
async def upload_video(file: UploadFile = File(...), title: str = Form(...)):
    # Basic validation: ensure it's an image
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video!")
    
    # Create a local path to save the video
    video_file_location = f"videos/{file.filename}"
    os.makedirs("videos", exist_ok=True)
    
    with open(video_file_location, "wb+") as file_object:
        # Stream the file content to disk
        shutil.copyfileobj(file.file, file_object)
    
    return {"info": f"Video '{title}' saved at {video_file_location}"}


@router.post('/thumbnail')
async def upload_thumbnail(file: UploadFile = File(...)):
    # Basic validation: ensure it's an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image!")
    
    # Create a local path to save the video
    thumbnail_file_location = f"thumbnails/{file.filename}"
    os.makedirs("thumbnails", exist_ok=True)
    
    with open(thumbnail_file_location, "wb+") as file_object:
        # Stream the file content to disk
        shutil.copyfileobj(file.file, file_object)
    
    return {"info": f"Video thumbnail {file.filename} saved at {thumbnail_file_location}"}
