from app.exceptions.base import AppException


class VideoPublishError(AppException):
    status_code = 400
    error_code = "VIDEO_PUBLISH_FAILED"
    message = "Failed to publish video"


class VideoNotFound(AppException):
    status_code = 404
    error_code = "VIDEO_NOT_FOUND"
    message = "Video not found."


class VideoPublishError(AppException):
    status_code = 400
    error_code = "VIDEO_PUBLISH_FAILED"
    message = "Failed to publish video."


class VideoArchiveFailed(AppException):
    status_code = 400
    error_code = "VIDEO_ARCHIVE_FAILED"
    message = "Failed to archive video."


class DuplicateEntryError(AppException):
    status_code = 409
    error_code = "DUPLICATE_ENTRY"
    message = "Duplicate entry."


class NoImageInRequest(AppException):
    status_code = 400
    error_code = "NO_IMAGE_IN_REQUEST"
    message = "Thumbnail image not found in request."


class ThumbnailAlreadyExists(AppException):
    status_code = 409
    error_code = "THUMBNAIL_ALREADY_EXISTS"
    message = "Video already has a thumbnail."
