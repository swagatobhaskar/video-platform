from pydantic import BaseModel, Field
from uuid import UUID
from pathlib import PurePosixPath

class NewTranscodedUploadRequest(BaseModel):
    # All optional so existing callers that send no body/fields keep working.
    title: str | None = Field(default=None, max_length=255)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    codec: str | None = Field(default=None, max_length=64)
    fps: float | None = Field(default=None, gt=0)
    bitrate: int | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)

class TranscodedFileRequest(BaseModel):
    file_id: str = Field(min_length=1, max_length=64)
    relative_path: str = Field(min_length=1, max_length=1024)
    size_bytes: int = Field(ge=0)
    content_type: str = Field(min_length=1, max_length=255)

class PresignTranscodedFilesRequest(BaseModel):
    transcoded_upload_session_id: UUID
    files: list[TranscodedFileRequest] = Field(min_length=1, max_length=100)

class PresignedTranscodedFile(BaseModel):
    file_id: str
    object_key: str
    upload_url: str
    # new
    already_uploaded: bool = False

class PresignTranscodedFilesResponse(BaseModel):
    files: list[PresignedTranscodedFile]

class CompleteTranscodedUploadRequest(BaseModel):
    transcoded_upload_session_id: UUID

class RecordUploadedFileRequest(BaseModel):
    transcoded_upload_session_id: UUID
    file_id: str = Field(min_length=1, max_length=64)

def validate_transcoded_relative_path(relative_path: str) -> None:

    path = PurePosixPath(relative_path)

    if path.is_absolute():
        raise ValueError("Absolute paths are not allowed")

    if ".." in path.parts:
        raise ValueError("Parent directory traversal is not allowed")

    parts = path.parts

    if len(parts) < 3:
        raise ValueError("Invalid transcoded file path")

    # my-video / dash / filename
    if parts[1] != "dash":
        raise ValueError("Transcoded files must be inside dash/")

    filename = parts[-1]

    allowed_extensions = {".m4s", ".mp4", ".m3u8", ".mpd",}

    if (PurePosixPath(filename).suffix.lower() not in allowed_extensions):
        raise ValueError(f"Unsupported transcoded file: {filename}")
    