from pydantic import BaseModel, field_validator
from app.core.validators import validate_password, validate_email

class UserRegister(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_validation(cls, v):
        return validate_email(v)

    @field_validator("password")
    @classmethod
    def password_validation(cls, v):
        return validate_password(v)


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_validation(cls, v):
        return validate_email(v)

    @field_validator("password")
    @classmethod
    def password_validation(cls, v):
        return validate_password(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"