from pydantic import BaseModel, EmailStr
from datetime import date, datetime

from core.constants import RoleSlug


class RoleSchema(BaseModel):
    id: int
    slug: str
    title: str


class UserLightSchema(BaseModel):
    id: int
    first_name: str
    email: str
    is_deceased: bool


class UserSchema(BaseModel):
    id: int
    first_name: str
    email: str
    date_of_birth: date
    is_deceased: bool
    email_verified: bool
    roles: list[RoleSchema]
    family: list[UserLightSchema]
    verificator: UserLightSchema | None = None
    created_at: datetime
    updated_at: datetime


class UserCreateSchema(BaseModel):
    email: EmailStr
    first_name: str
    password: str
    date_of_birth: date


class UserUpdateSchema(BaseModel):
    first_name: str | None = None
    date_of_birth: date | None = None


class UserFilterSchema(BaseModel):
    email: str | None = None
    role_slug: RoleSlug | None = None


## Internal
class UserUpdateInternalSchema(UserUpdateSchema):
    password: str | None = None
    email_verified: bool | None = None
    verificator_id: int | None = None
    is_deceased: bool | None = None


class CurrentUserSchema(BaseModel):
    id: int
    is_active: bool
    email_verified: bool
    first_name: str
    verificator_id: int | None = None
    email: EmailStr
    roles: list[RoleSchema]


class UserAuthSchema(BaseModel):
    id: int
    email_verified: bool
    password: str
    email: EmailStr
    is_active: bool
