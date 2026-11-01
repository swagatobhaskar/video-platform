from app.exceptions.base import AppException

# class CategoryAlreadyExists(AppException):
#     status_code = 409
#     error_code = "CATEGORY_ALREADY_EXISTS"
#     message = "Category already exists."

class VideoTranscriptNotFound(AppException):
    status_code = 404
    error_code = "VIDEO_TRANSCRIPT_NOT_FOUND"
    message = "Video Transcript not found."

# class VideoAlreadyLinked(AppException):
#     status_code = 409
#     error_code = "VIDEO_ALREADY_LINKED"
#     message = "Video is already linked to the category."
    