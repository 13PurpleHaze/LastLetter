from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date, datetime

from core.constants import RoleSlug


class RoleSchema(BaseModel):
    id: int
    slug: str
    title: str


class FamilyMemberSchema(BaseModel):
    id: int
    first_name: str
    email: str
    roles: list[RoleSchema]


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
    family: list[FamilyMemberSchema]
    verificator_id: int | None
    created_at: datetime
    updated_at: datetime


class UserCreateSchema(BaseModel):
    email: EmailStr
    first_name: str
    password: str
    date_of_birth: date


class UserUpdateSchema(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    password: str | None = None
    date_of_birth: date | None = None
    email_verified: bool | None = None
    is_deceased: bool | None = None
    verificator_id: int | None = None


class CurrentUserSchema(BaseModel):
    id: int
    first_name: str
    email: str
    date_of_birth: date
    roles: list[RoleSchema]
    is_active: bool
    email_verified: bool
    family: list[FamilyMemberSchema]
    verificator_id: int | None
    is_deceased: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "first_name": "Максим",
                "email": "max@example.com",
                "date_of_birth": str(date(1999, 1, 1)),
                "is_active": True,
                "email_verified": True,
                "roles": [
                    {"id": 1, "slug": "parent", "title": "Родитель"},
                    {"id": 2, "slug": "child", "title": "Ребенок"},
                ],
                "family": [
                    {
                        "id": 67,
                        "first_name": "Август",
                        "email": "agust@mail.com",
                        "roles": [
                            {"id": 1, "slug": "parent", "title": "Родитель"},
                            {"id": 2, "slug": "child", "title": "Ребенок"},
                        ],
                    },
                ],
            }
        }
    )


class UserFilterSchema(BaseModel):
    email: str | None = None
    role_slug: RoleSlug | None = None
