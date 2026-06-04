from pydantic import BaseModel, EmailStr
from datetime import date, datetime


class RoleSchema(BaseModel):
    id: int
    slug: str
    title: str


class UserSchema(BaseModel):
    id: int
    first_name: str
    email: str
    password: str
    date_of_birth: date
    is_deceased: bool
    email_verified: bool
    is_active: bool
    roles: list[RoleSchema]
    created_at: datetime
    updated_at: datetime


class UserCreateSchema(BaseModel):
    email: EmailStr
    first_name: str
    password: str
    date_of_birth: date


class UserUpdateSchema(BaseModel):
    email: EmailStr | None
    first_name: str | None
    password: str | None
    date_of_birth: date | None


class CurrentUserSchema(BaseModel):
    id: int
    first_name: str
    email: str
    date_of_birth: date
    roles: list[RoleSchema]
    is_active: bool
    email_verified: bool
