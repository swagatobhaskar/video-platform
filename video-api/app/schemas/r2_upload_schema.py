from pydantic import BaseModel, Field

class InitiateUploadRequest(BaseModel):
    fileName: str
    contentType: str
    
class Part(BaseModel):    
    ETag: str = Field(..., min_length=1)
    PartNumber: int = Field(..., gt=0)
    
class PartRequest(BaseModel):
    key: str
    uploadId: str
    partNumber: int
    
class CompleteRequest(BaseModel):
    key: str
    uploadId: str
    parts: list[Part]
    
class AbortRequest(BaseModel):
    key: str
    uploadId: str
