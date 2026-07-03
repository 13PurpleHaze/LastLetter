from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from core.scheduler import scheduler
from modules.capsules.constants import ALLOWED_EXTENSIONS
from modules.capsules.exceptions import (
    CapsuleNotFoundError,
    PermissionDeniedError,
    ContentNotFoundError,
    ObjectNotFoundError,
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
    CapsuleUpdateSchema,
    CapsuleLightSchema,
    UserCapsuleSchema,
)
import uuid

from modules.email.tasks import send_user_capsule_email_task
from modules.user.schemas import CurrentUserSchema
from services.s3.client import S3Client
from infrastructure.filter import Filter
import os
from datetime import datetime


class CapsuleService:
    def __init__(self, repository: CapsuleRepository):
        self.repository = repository

    async def get_capsules_by_recipient(
        self,
        current_user: CurrentUserSchema,
        filter: Filter,
        pagination: PaginationParams,
    ) -> tuple[list[CapsuleLightSchema], PageMetaSchema]:
        capsules, total = await self.repository.get_capsules_by_recipient(
            recipient_id=current_user.id,
            filter=filter,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PageMetaSchema(
            limit=pagination.limit,
            offset=pagination.offset,
            total=total,
        )
        return capsules, meta

    async def get_capsule_by_recipient_by_id(
        self, current_user: CurrentUserSchema, capsule_id: int
    ):
        return await self.repository.get_capsule_by_recipient_by_id(
            capsule_id=capsule_id, recipient_id=current_user.id
        )

    async def _get_capsules_by_creator_with_relations(
        self,
        current_user: CurrentUserSchema,
    ) -> list[CapsuleSchema]:
        return await self.repository.get_capsules_by_creator_with_relations(
            creator_id=current_user.id
        )

    async def get_capsules_by_creator(
        self,
        current_user: CurrentUserSchema,
        filter: Filter,
        pagination: PaginationParams,
    ) -> tuple[list[CapsuleLightSchema], PageMetaSchema]:
        capsules, total = await self.repository.get_capsules_by_creator(
            creator_id=current_user.id,
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

    async def get_capsule_by_id(
        self, capsule_id: int, current_user: CurrentUserSchema
    ) -> CapsuleSchema | None:
        capsule = await self.repository.get_capsule_with_relations_by_id(
            capsule_id=capsule_id
        )
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        is_creator = capsule.creator.id == current_user.id
        is_recipient = any(u.id == current_user.id for u in capsule.users)
        if not (is_creator or is_recipient):
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if is_creator:
            return capsule
        if is_recipient:
            if not capsule.creator.is_deceased:
                raise CapsuleNotFoundError(capsule_id)
            if capsule.send_at and datetime.now() < capsule.send_at:
                raise CapsuleNotFoundError(capsule_id)
        return capsule

    async def create_capsule(
        self, capsule_create: CapsuleCreateSchema, creator_id: int
    ) -> CapsuleLightSchema:
        return await self.repository.create_capsule(
            capsule_create=capsule_create, creator_id=creator_id
        )

    async def update_capsule(
        self,
        capsule_id: int,
        capsule_update: CapsuleUpdateSchema,
        current_user: CurrentUserSchema,
    ) -> CapsuleSchema | None:
        capsule = await self.repository.get_capsule_by_id(capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        updated_capsule = await self.repository.update_capsule(
            capsule_id=capsule_id, capsule_update=capsule_update
        )
        return updated_capsule

    async def delete_capsule(self, capsule_id: int, current_user: CurrentUserSchema):
        capsule = await self.repository.get_capsule_by_id(capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        await self.repository.delete_capsule(capsule_id=capsule_id)

    async def attach_user(
        self,
        capsule_id: int,
        user_attach: CapsuleUserAttachSchema,
        current_user: CurrentUserSchema,
    ) -> UserCapsuleSchema:
        allowed = await self.repository.can_attach_user(
            capsule_id=capsule_id,
            current_user_id=current_user.id,
            target_user_id=user_attach.user_id,
        )

        if not allowed:
            raise PermissionDeniedError()

        return await self.repository.attach_user(
            user_id=user_attach.user_id,
            capsule_id=capsule_id,
        )

    async def detach_user(
        self,
        capsule_id: int,
        user_id,
        current_user: CurrentUserSchema,
    ):
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        await self.repository.detach_user(
            user_id=user_id,
            capsule_id=capsule_id,
        )

    async def get_upload_url(
        self,
        capsule_id: int,
        request: UploadUrlRequestSchema,
        current_user: CurrentUserSchema,
        s3_client: S3Client,
    ) -> UploadUrlResponseSchema:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)

        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()

        ext = os.path.splitext(request.filename)[1].lower().lstrip(".")

        if ext not in ALLOWED_EXTENSIONS:
            raise PermissionDeniedError()
        object_key = f"capsules/{capsule_id}/{uuid.uuid4()}.{ext}"
        url = await s3_client.generate_upload_url(
            object_key=object_key, content_type=request.content_type, expires_in=400
        )
        return UploadUrlResponseSchema(url=url, expires_in=400, object_key=object_key)

    async def confirm_upload_content(
        self,
        content_create: ContentCreateSchema,
        capsule_id: int,
        current_user: CurrentUserSchema,
        s3_client: S3Client,
    ) -> ContentSchema:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()
        object_exists = await s3_client.object_exists(
            object_key=content_create.object_key
        )
        if not object_exists:
            raise ObjectNotFoundError(object_key=content_create.object_key)
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
        capsule = await self.repository.get_capsule_with_relations_by_id(
            capsule_id=capsule_id
        )
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        is_creator = capsule.creator.id == current_user.id
        is_recipient = any(u.id == current_user.id for u in capsule.users)
        if not (is_recipient or is_creator):
            raise PermissionDeniedError()
        content = await self.repository.get_content_by_id(content_id=content_id)
        if not content:
            raise ContentNotFoundError(content_id=content_id)
        if content.capsule_id != capsule_id:
            raise PermissionDeniedError()

        download_url = await s3_client.generate_download_url(content.object_key)
        return UploadUrlResponseSchema(
            url=download_url, expires_in=3600, object_key=content.object_key
        )

    async def delete_content(
        self,
        capsule_id: int,
        content_id: int,
        current_user: CurrentUserSchema,
        s3_client: S3Client,
    ) -> None:
        content = await self.repository.get_content_by_id(content_id)
        if not content:
            raise ContentNotFoundError(content_id=content_id)
        capsule = await self.repository.get_capsule_by_id(content.capsule_id)
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        if capsule.creator_id != current_user.id:
            raise PermissionDeniedError()

        await self.repository.delete_content(
            content_id=content_id, capsule_id=capsule_id
        )

        await s3_client.delete_object(content.object_key)

    async def release_capsules(self, creator: CurrentUserSchema):
        capsules = await self._get_capsules_by_creator_with_relations(
            current_user=creator,
        )

        for capsule in capsules:
            if capsule.send_at:
                scheduler.add_job(
                    func=self._send_capsule_to_users,
                    trigger="date",
                    run_date=capsule.send_at,
                    args=[capsule, creator.first_name],
                    id=f"capsule-{capsule.id}",
                    replace_existing=True,
                )
            else:
                await self._send_capsule_to_users(
                    capsule=capsule, creator_name=creator.first_name
                )

    async def _send_capsule_to_users(self, capsule: CapsuleSchema, creator_name: str):
        for user in capsule.users:
            send_user_capsule_email_task.send(
                to_email=user.email,
                user_name=creator_name,
                capsule_name=capsule.title,
            )

    @staticmethod
    def get_allowed_extensions() -> set[str]:
        return ALLOWED_EXTENSIONS
