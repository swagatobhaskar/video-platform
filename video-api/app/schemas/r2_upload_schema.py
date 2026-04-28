from pydantic import BaseModel

class InitiateUploadRequest(BaseModel):
    fileName: str
    contentType: str
    
class PartRequest(BaseModel):
    key: str
    uploadId: str
    partNumber: int
    
class CompleteRequest(BaseModel):
    key: str
    uploadId: str
    parts: list
    