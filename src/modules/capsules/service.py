from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from modules.auth.exception import UserNotFoundError
from modules.capsules.exceptions import (
    CapsuleNotFoundError,
    PermissionDeniedError,
    ContentNotFoundError,
)
from modules.capsules.repository import CapsuleRepository
from modules.capsules.schemas import (
    CapsuleCreateSchema,
    CapsuleSchema,
    ContentSchema,
    UploadUrlRequestSchema,
    UploadUrlResponseSchema,
    ContentCreateSchema,
    CapsuleUserAttachSchema,
    CapsuleUserSchema,
    CapsuleUpdateSchema,
)
from datetime import datetime
import uuid
from modules.user.schemas import CurrentUserSchema
from modules.user.service import UserService
from services.s3.client import S3Client
from infrastructure.filter import Filter


class CapsuleService:
    def __init__(self, repository: CapsuleRepository):
        self.repository = repository

    async def get_capsules_by_user(
        self,
        current_user: CurrentUserSchema,
        filter: Filter,
        pagination: PaginationParams,
    ) -> tuple[list[CapsuleSchema], PageMetaSchema]:
        capsules, total = await self.repository.get_capsules_by_user(
            current_user=current_user,
            filter=filter,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PageMetaSchema(
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        return capsules, meta

    async def create_capsule(
        self, capsule_create: CapsuleCreateSchema, creator_id: int
    ) -> CapsuleSchema:
        return await self.repository.create_capsule(
            capsule_create=capsule_create, creator_id=creator_id
        )

    async def update_capsule(
        self,
        capsule_id: int,
        capsule_update: CapsuleUpdateSchema,
        current_user: CurrentUserSchema,
    ) -> CapsuleSchema:
        updated_capsule = await self.repository.update_capsule_text(
            capsule_id=capsule_id, capsule_update=capsule_update
        )
        if not updated_capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if updated_capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        return updated_capsule

    async def delete_capsule(self, capsule_id: int, current_user: CurrentUserSchema):
        capsule = await self.repository.get_capsule_by_id(capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        await self.repository.delete_capsule(capsule_id=capsule_id)

    async def get_content_by_id(self, content_id: int) -> ContentSchema | None:
        return await self.repository.get_content_by_id(content_id=content_id)

    async def get_capsule_by_id(
        self, capsule_id: int, current_user: CurrentUserSchema
    ) -> CapsuleSchema | None:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        return capsule

    async def attach_user(
        self,
        capsule_id: int,
        user_attach: CapsuleUserAttachSchema,
        current_user: CurrentUserSchema,
        user_service: UserService,
    ) -> None:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        user = await user_service.get_user_by_id(user_id=user_attach.user_id)
        if not user:
            raise UserNotFoundError()
        await self.repository.attach_user(
            user_id=user_attach.user_id,
            capsule_id=capsule_id,
            send_at=user_attach.send_at,
        )

    async def detach_user(
        self,
        capsule_id: int,
        user_id,
        current_user: CurrentUserSchema,
        user_service: UserService,
    ) -> None:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        user = await user_service.get_user_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError()
        await self.repository.detach_user(
            user_id=user_id,
            capsule_id=capsule_id,
        )

    async def update_capsule_send_date(
        self,
        capsule_id: int,
        user_id: int,
        date: datetime,
        current_user: CurrentUserSchema,
    ) -> CapsuleUserSchema | None:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        user_capsule = await self.repository.get_capsule_user_by_ids(
            capsule_id=capsule_id, user_id=user_id
        )
        if not user_capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        return await self.repository.update_send_date(
            send_at=date, capsule_id=capsule_id, user_id=user_id
        )

    async def get_upload_url(
        self,
        capsule_id: int,
        request: UploadUrlRequestSchema,
        current_user: CurrentUserSchema,
        s3client: S3Client,
    ) -> UploadUrlResponseSchema:
        await self.get_capsule_by_id(capsule_id=capsule_id, current_user=current_user)
        ext = request.filename.split(".")[-1].lower()
        object_key = f"capsules/{capsule_id}/{uuid.uuid4()}.{ext}"
        url = await s3client.generate_upload_url(
            object_key=object_key, content_type=request.content_type, expires_in=400
        )
        return UploadUrlResponseSchema(url=url, expires_in=400, object_key=object_key)

    async def confirm_upload_content(
        self,
        content_create: ContentCreateSchema,
        capsule_id: int,
        current_user: CurrentUserSchema,
    ) -> ContentSchema:
        await self.get_capsule_by_id(capsule_id=capsule_id, current_user=current_user)
        return await self.repository.create_content(
            content_create=content_create, capsule_id=capsule_id
        )

    async def get_download_url(
        self,
        capsule_id: int,
        content_id: int,
        current_user: CurrentUserSchema,
        s3_client: S3Client,
    ) -> UploadUrlResponseSchema:
        await self.get_capsule_by_id(capsule_id=capsule_id, current_user=current_user)
        content = await self.get_content_by_id(content_id=content_id)
        if not content:
            raise ContentNotFoundError(content_id=content_id)
        download_url = await s3_client.generate_download_url(content.object_key)
        return UploadUrlResponseSchema(
            url=download_url, expires_in=3600, object_key=content.object_key
        )
