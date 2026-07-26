from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid
import enum
from .user_schema import UserOut

class LoginInput(BaseModel):
    email: EmailStr
    password: str
    
# class UserLogin(BaseModel):
#     message: str
#     access_token: str
#     refresh_token: str
#     csrf_token: str
#     token_type: str

# class UserOutWithToken(BaseModel):
#     message: str
#     access_token: str
#     refresh_token: str
#     token_type: str
#     user: UserOut


# class TokenSchema(BaseModel):
#     access_token: str
#     token_type: str

class RoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class UserDetail(BaseModel):
    id: uuid.UUID
    username: str | None = None
    email: EmailStr
    role: RoleEnum
    created_at: datetime
    updated_at: datetime
