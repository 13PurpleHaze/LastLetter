from datetime import datetime
from pydantic import BaseModel
from modules.user.schemas import UserLightSchema


class ContentSchema(BaseModel):
    id: int
    object_key: str
    content_type: str
    size_bytes: int
    order_index: int
    capsule_id: int


# Capsule
class CapsuleLightSchema(BaseModel):
    id: int
    title: str
    text: str | None
    send_at: datetime | None
    creator_id: int
    created_at: datetime
    updated_at: datetime


class CapsuleSchema(BaseModel):
    id: int
    title: str
    text: str | None = None
    creator: UserLightSchema
    users: list[UserLightSchema]
    contents: list[ContentSchema]
    send_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CapsuleCreateSchema(BaseModel):
    title: str
    text: str | None


class CapsuleUserAttachSchema(BaseModel):
    user_id: int


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
    send_at: datetime | None = None


class UserCapsuleSchema(BaseModel):
    capsule_id: int
    user_id: int


class CapsuleUpdateInternalSchema(CapsuleUpdateSchema):
    sent_at: datetime | None = None
