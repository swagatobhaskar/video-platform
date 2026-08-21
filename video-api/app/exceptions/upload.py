class UploadServiceError(Exception):
    """Base exception for upload service errors."""


class NewUploadCreationFailed(UploadServiceError):
    """Failed to create a new upload record."""


class UploadSessionNotFound(UploadServiceError):
    """Upload session does not exist."""


class UploadAlreadyCompleted(UploadServiceError):
    """Upload has already been completed."""


class InvalidUploadState(UploadServiceError):
    """Upload is not in a state that permits the requested operation."""
    