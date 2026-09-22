from app.exceptions.base import AppException

class SeriesNotFound(AppException):
    status_code = 404
    error_code = "SERIES_NOT_FOUND"
    message = "Series not found."


class SeriesAlreadyExists(AppException):
    status_code = 409
    error_code = "SERIES_ALREADY_EXISTS"
    message = "Series already exists."


class VideoAlreadyInTheSeries(AppException):
    status_code = 409
    error_code = "VIDEO_ALREADY_IN_SERIES"
    message = "Video is already in the series."
    