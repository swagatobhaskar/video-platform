from pydantic import BaseModel, EmailStr

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