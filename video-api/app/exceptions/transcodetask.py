from app.exceptions.base import AppException

class TranscodeTaskNotFound(AppException):
    status_code = 404
    error_code = "TRANSCODE_TASK_NOT_FOUND"
    message = "Transcode task not found."


"""
If it's an internal consistency error rather than something caused by the client's request,
you might eventually want it to be a 500 instead.
But 409 is reasonable if it's validating resource relationships coming from a request.
"""
class TranscodeTaskMismatch(AppException):
    status_code = 409
    error_code = "TRANSCODE_TASK_MISMATCH"
    message = "Transcode task does not belong to the requested video."
