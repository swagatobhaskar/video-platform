import os
import shutil
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from celery.result import AsyncResult

from app.schemas.r2_upload_schema import CompleteRequest, PartRequest, InitiateUploadRequest, AbortRequest
from app.utils.r2_helper import s3

from app.celery_worker import celery
from app.tasks.transcode.transcode_task import process_video_transcoding

router = APIRouter(prefix="/api/upload", tags=["upload"])

# @router.post('/video')
# async def upload_video(file: UploadFile = File(...), title: str = Form(...)):
#     # Basic validation: ensure it's an image
#     if not file.content_type.startswith("video/"):
#         raise HTTPException(status_code=400, detail="File must be a video!")
    
#     # Create a local path to save the video
#     video_file_location = f"videos/{file.filename}"
#     os.makedirs("videos", exist_ok=True)
    
#     with open(video_file_location, "wb+") as file_object:
#         # Stream the file content to disk
#         shutil.copyfileobj(file.file, file_object)
    
#     return {"info": f"Video '{title}' saved at {video_file_location}"}


# @router.post('/thumbnail')
# async def upload_thumbnail(file: UploadFile = File(...)):
#     # Basic validation: ensure it's an image
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="File must be an image!")
    
#     # Create a local path to save the video
#     thumbnail_file_location = f"thumbnails/{file.filename}"
#     os.makedirs("thumbnails", exist_ok=True)
    
#     with open(thumbnail_file_location, "wb+") as file_object:
#         # Stream the file content to disk
#         shutil.copyfileobj(file.file, file_object)
    
#     return {"info": f"Video thumbnail {file.filename} saved at {thumbnail_file_location}"}


RAW_VIDEO_BUCKET: str = 'raw-video-upload-bucket'

@router.post('/initiate-upload')
def initiate_upload(req: InitiateUploadRequest):
    
    # Use {UUID}-{filename} instead of just filename
    import uuid
    unique_filename_key = f"{uuid.uuid4()}-{req.fileName}"
    
    response = s3.create_multipart_upload(
        Bucket=RAW_VIDEO_BUCKET,
        Key=unique_filename_key, # req.fileName,
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


def get_uploaded_parts(s3, bucket: str, key: str, uploadId: str):
    response = s3.list_parts(
        Bucket=bucket,
        Key=key,
        UploadId=uploadId
    )
    
    return response.get("Parts", [])

@router.post("/complete-upload")
def complete_upload(req: CompleteRequest):
    
    # Later Additions:
        # Ordering check
        # ETag validation
        # Storage verification
        
    try:
        # Verify actual uploaded parts with R2
        uploaded_parts = get_uploaded_parts(
            s3,
            RAW_VIDEO_BUCKET,
            req.key,
            req.uploadId
        )
        
        if len(uploaded_parts) != len(req.parts):
            raise ValueError("Mismatch between uploaded parts and client parts")
        
        # Complete upload
        s3.complete_multipart_upload(
            Bucket=RAW_VIDEO_BUCKET,
            Key=req.key,
            UploadId=req.uploadId,
            MultipartUpload={
                # "Parts": req.parts,  # [{ETag, PartNumber}]
                "Parts": [
                    {
                        "ETag": part.ETag,
                        "PartNumber": part.PartNumber
                    }
                    for part in req.parts
                ]
            },
        )
        
        # start a celery task
        task = process_video_transcoding.delay( # type: ignore
            key=req.key,
            bucket=RAW_VIDEO_BUCKET    
        )
        
        return {
            "success": True,
            "taskId": task.id,
            "status": "upload completed",
        }
    
    except Exception as e:
        return {"error": str(e)}

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


@router.get("/processing-status/{transcode_task_id}")
def get_transcode_processing_status(transcode_task_id: str):
    status = AsyncResult(transcode_task_id, app=celery)
        
    return {
        "task_id": transcode_task_id,
        "status": status.status,
        "result": status.result
    }
