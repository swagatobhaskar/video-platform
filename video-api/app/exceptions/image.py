from app.exceptions.base import AppException


class ImageTooLargeError(AppException):
    status_code = 413
    error_code = "IMAGE_TOO_LARGE"
    message = "Image is too large."


class UnsupportedImageFormatError(AppException):
    status_code = 415
    error_code = "UNSUPPORTED_IMAGE_FORMAT"
    message = "Unsupported image format."


class InvalidImageError(AppException):
    status_code = 400
    error_code = "INVALID_IMAGE"
    message = "Invalid image."


class CorruptedImageError(AppException):
    status_code = 400
    error_code = "CORRUPTED_IMAGE"
    message = "Image is corrupted or could not be processed."
