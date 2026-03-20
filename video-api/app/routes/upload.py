import os
import shutil
from fastapi import APIRouter, File, UploadFile, Form

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post('/')
async def upload_video(file: UploadFile = File(...), title: str = Form(...)):
    # Create a local path to save the video
    file_location = f"videos/{file.filename}"
    os.makedirs("videos", exist_ok=True)
    
    with open(file_location, "wb+") as file_object:
        # Stream the file content to disk
        shutil.copyfileobj(file.file, file_object)
    
    return {"info": f"Video '{title}' saved at {file_location}"}
