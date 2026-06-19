from datetime import datetime
from pydantic import BaseModel, field_validator, ValidationError
from modules.user.schemas import CurrentUserSchema


class ContentSchema(BaseModel):
    id: int
    object_key: str
    content_type: str
    size_bytes: int
    order_index: int


## Capsule
class CapsuleSchema(BaseModel):
    id: int
    title: str
    text: str | None
    creator_id: int
    users: list[CurrentUserSchema]
    contents: list[ContentSchema]
    created_at: datetime
    updated_at: datetime


class CapsuleCreateSchema(BaseModel):
    title: str
    text: str | None


class CapsuleUserAttachSchema(BaseModel):
    user_id: int
    send_at: datetime | None = None


class CapsuleUpdateDateSchema(BaseModel):
    send_at: datetime

    @field_validator("send_at")
    @classmethod
    def validate_send_at(cls, v):
        if v < datetime.now():
            raise ValidationError("Поле send_at должно быть больше текущей даты")
        return v


class CapsuleFilterSchema(BaseModel):
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


## Content
class UploadUrlRequestSchema(BaseModel):
    filename: str
    content_type: str


class UploadUrlResponseSchema(BaseModel):
    url: str
    object_key: str
    expires_in: int


class ContentCreateSchema(BaseModel):
    object_key: str
    content_type: str
    size_bytes: int
    order_index: int


class CapsuleUpdateSchema(BaseModel):
    title: str | None = None
    text: str | None = None


class CapsuleUserSchema(BaseModel):
    capsule_id: int
    user_id: int
    send_at: datetime | None
    sent_at: datetime | None
    is_sent: bool
