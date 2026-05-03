import os
import shutil
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from app.schemas.r2_upload_schema import CompleteRequest, PartRequest, InitiateUploadRequest, AbortRequest
from app.utils.r2_helper import s3

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


RAW_VIDEO_BUCKET: str = 'raw-video-upload-bucket'

@router.post('/initiate-upload')
def initiate_upload(req: InitiateUploadRequest):
    response = s3.create_multipart_upload(
        Bucket=RAW_VIDEO_BUCKET,
        Key=req.fileName,
        ContentType=req.contentType
    )
    print("Initiate Upload Response: ", response)
    
    return {
        "uploadId": response["UploadId"],
        "key": response["Key"],
    }

@router.post("/get-presigned-url")
def get_presigned_url(req: PartRequest):
    url = s3.generate_presigned_url(
        ClientMethod="upload_part",
        Params={
            "Bucket": RAW_VIDEO_BUCKET,
            "Key": req.key,
            "UploadId": req.uploadId,
            "PartNumber": req.partNumber,
        },
        ExpiresIn=3600,
    )
    print("Generated presigned URL: ", url)
    return {"uploadUrl": url}

@router.post("/complete-upload")
def complete_upload(req: CompleteRequest):
    s3.complete_multipart_upload(
        Bucket=RAW_VIDEO_BUCKET,
        Key=req.key,
        UploadId=req.uploadId,
        MultipartUpload={
            "Parts": req.parts,  # [{ETag, PartNumber}]
        },
    )
    return {"success": True}

@router.post("/abort-upload")
def abort_upload(req: AbortRequest):
    try:
        s3.abort_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
        )
        return {"success": True, "status": "aborted"}
    except Exception as e:
        return {"error": str(e)}
    