from datetime import date

from pydantic import BaseModel, EmailStr


class UserRegisterSchema(BaseModel):
    email: EmailStr
    first_name: str
    password: str
    date_of_birth: date
    is_parent: bool
    is_child: bool = False
    is_verifier: bool = False


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserVerifySchema(BaseModel):
    email: EmailStr


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
