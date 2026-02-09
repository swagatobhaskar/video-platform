from datetime import datetime
import re
from uuid import UUID
from typing_extensions import Self
from pydantic import (
    BaseModel, EmailStr, ConfigDict, field_validator, model_validator
    )

class UserBase(BaseModel):
    email: EmailStr
    
    # Define a validator for the email field
    @field_validator("email")
    def check_email(cls, value):
        # use a regex to check that the email has a valid format
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email address")
        return value
    
class UserCreate(UserBase):
    password: str
    
    # Define a validator for the password field
    @field_validator("password")
    def check_password(cls, value):
        # convert the password to a string if it is not already
        value = str(value)
        # check that the password has at least 8 characters, one uppercase letter, one lowercase letter, and one digit
        if len(value) < 8:
            raise ValueError("Password must have at least 8 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must have at least one uppercase letter")
        if not any(c.islower() for c in value):
            raise ValueError("Password must have at least one lowercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must have at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must include at least one special character")
        return value
    
    
class UserOut(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    # created_at: datetime
    # updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    # class Config:
    #     from_attributes = True
    

# class UserEdit(BaseModel):
#     email: EmailStr | None = None
#     password: str | None = None
    

class UserPatch(BaseModel):
    email: EmailStr | None = None
    old_password: str | None = None
    new_password: str | None = None
    confirm_password: str | None = None

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        # check if old_password is present
        if self.old_password:
            # check if new_password and confirm_password are both present
            if not self.new_password or not self.confirm_password:
                raise ValueError('New Password and Confirm Password must be entered!')
        if self.new_password != self.confirm_password:
            raise ValueError('New Password and Confirm Password do not match')
        return self

class UpdateProfileResponse(BaseModel):
    message: str
    status_code: int
    user: UserOut
    