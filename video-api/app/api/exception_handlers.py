from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.video import VideoNotFound, VideoPublishError, VideoArchiveFailed, DuplicateEntryError, NoImageInRequest, ThumbnailAlreadyExists
from app.exceptions.series import SeriesAlreadyExists, SeriesNotFound, VideoAlreadyInTheSeries
from app.exceptions.upload import UploadSessionNotFound, UploadAlreadyCompleted, NewUploadCreationFailed
from app.exceptions.storage import StorageProviderError
from app.exceptions.category import CategoryAlreadyExists, CategoryNotFound, VideoAlreadyLinked


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

async def new_upload_creation_failed_handler(request: Request, exc: NewUploadCreationFailed):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "UPLOAD_CREATION_FAILED",
            "message": "Failed to create new video upload session.",
        },
    )

# @app.exception_handler(StorageProviderError)
async def storage_provider_error_handler(
    request: Request,
    exc: StorageProviderError,
):
    return JSONResponse(
        status_code=502,
        content={
            "detail": str(exc),
        },
    )


# @app.exception_handler(CategoryAlreadyExists)
async def category_exists_handler(
    request: Request,
    exc: CategoryAlreadyExists,
):
    return JSONResponse(
        status_code=409,
        content={"detail": "Category already exists"},
    )

async def category_not_found_handler(
    request: Request,
    exc: CategoryNotFound,
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Category not found"},
    )

async def video_not_found_handler(
    request: Request,
    exc: VideoNotFound,
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Video not found"},
    )

async def video_publish_error_handler(
    request: Request,
    exc: VideoPublishError,
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Failed to publish video",
        },
    )

async def video_archive_error_handler(
    request: Request,
    exc: VideoArchiveFailed,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Failed to archive video"},
    )

async def video_metadata_duplicate_entry_handler(
    request: Request,
    exc: DuplicateEntryError,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Duplicate entry."},
    )

async def video_already_linked_to_category_handler(
    request: Request,
    exc: VideoAlreadyLinked,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Video already linked to the category"},
    )

async def video_already_in_series_handler(
    request: Request,
    exc: VideoAlreadyInTheSeries,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Video is already in the Series"},
    )

async def series_not_found_handler(
    request: Request,
    exc: SeriesNotFound,
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Series not found"},
    )

async def series_already_exists_handler(
    request: Request,
    exc: SeriesAlreadyExists,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Series already exists"},
    )


async def no_image_in_request_handler(
    request: Request,
    exc: NoImageInRequest,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Thumbnail image not found in request."},
    )

async def thumbnail_already_exists_handler(
    request: Request,
    exc: ThumbnailAlreadyExists,
):
    return JSONResponse(
        status_code=409,
        content={"detail": "Video already has a thumbnail."}
    )
