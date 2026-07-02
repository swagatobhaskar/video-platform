from uuid import UUID
from pydantic import BaseModel, Field

from app.database.models.video import LanguageEnum

class InitiateUploadRequest(BaseModel):
    fileName: str
    contentType: str
    fileSizeBytes: int
    totalParts: int
    categoryId: UUID | None = None
    language: LanguageEnum = LanguageEnum.BENGALI
    
class Part(BaseModel):    
    ETag: str = Field(..., min_length=1)
    PartNumber: int = Field(..., gt=0)
    SizeBytes: int | None = None
    
class PartRequest(BaseModel):
    key: str
    uploadId: str
    partNumber: int
    
class CompleteRequest(BaseModel):
    key: str
    uploadId: str | None = None
    videoId: str | None = None
    uploadSessionId: str | None = None
    parts: list[Part]
    
class AbortRequest(BaseModel):
    key: str
    uploadId: str
    videoId: str
