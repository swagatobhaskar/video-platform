from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.upload import UploadNotFound, UploadAlreadyCompleted


async def upload_not_found_handler(request: Request, exc: UploadNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "UPLOAD_NOT_FOUND",
            "message": "Upload session was not found.",
        },
    )


async def upload_already_completed_handler(
    request: Request,
    exc: UploadAlreadyCompleted,
):
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "error": "UPLOAD_ALREADY_COMPLETED",
            "message": "Upload has already been completed.",
        },
    )