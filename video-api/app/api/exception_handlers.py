from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions.base import AppException


async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content = {
            "success": False,
            "error": exc.error_code,
            "message": str(exc.message),
        },
    )
"""
async def upload_not_found_handler(request: Request, exc: UploadSessionNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "UPLOAD_SESSION_NOT_FOUND",
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
"""