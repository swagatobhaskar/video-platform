from app.exceptions.base import AppException


class NewUploadCreationFailed(AppException):
    status_code = 500
    error_code = "UPLOAD_CREATION_FAILED"
    message = "Failed to create new video upload session."


class UploadSessionNotFound(AppException):
    status_code = 404
    error_code = "UPLOAD_SESSION_NOT_FOUND"
    message = "Upload session was not found."


class UploadAlreadyCompleted(AppException):
    status_code = 409
    error_code = "UPLOAD_ALREADY_COMPLETED"
    message = "Upload has already been completed."


class InvalidUploadState(AppException):
    status_code = 409
    error_code = "INVALID_UPLOAD_STATE"
    message = "Upload is not in a state that permits the requested operation."
