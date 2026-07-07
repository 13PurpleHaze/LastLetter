from apscheduler.schedulers.asyncio import AsyncIOScheduler

from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from config import settings
from modules.capsules.constants import ALLOWED_EXTENSIONS
from modules.capsules.exceptions import (
    ObjectNotFoundError,
    CapsuleNotAllowAttachUser,
    CapsuleNotAllowedExtension,
)
from modules.capsules.policies import CapsulePolicy, ContentPolicy
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
from utils.content.get_extension import get_extension


class CapsuleService:
    def __init__(
        self,
        repository: CapsuleRepository,
        scheduler: AsyncIOScheduler,
    ):
        self.repository = repository
        self.scheduler = scheduler

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
        CapsulePolicy.can_view(
            capsule=capsule, user=current_user, capsule_id=capsule_id
        )
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
        CapsulePolicy.can_interact(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
        updated_capsule = await self.repository.update_capsule(
            capsule_id=capsule_id, capsule_update=capsule_update
        )
        return updated_capsule

    async def delete_capsule(self, capsule_id: int, current_user: CurrentUserSchema):
        capsule = await self.repository.get_capsule_by_id(capsule_id)
        CapsulePolicy.can_interact(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
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
            raise CapsuleNotAllowAttachUser(
                user_id=current_user.id, capsule_id=capsule_id
            )

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
        CapsulePolicy.can_interact(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
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
        CapsulePolicy.can_interact(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
        ext = get_extension(request.filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise CapsuleNotAllowedExtension(ext=ext)
        object_key = f"capsules/{capsule_id}/{uuid.uuid4()}.{ext}"
        url = await s3_client.generate_upload_url(
            object_key=object_key,
            content_type=request.content_type,
        )
        return UploadUrlResponseSchema(
            url=url,
            expires_in=settings.S3_LINK_EXPIRE_MINUTES * 60,
            object_key=object_key,
        )

    async def confirm_upload_content(
        self,
        content_create: ContentCreateSchema,
        capsule_id: int,
        current_user: CurrentUserSchema,
        s3_client: S3Client,
    ) -> ContentSchema:
        capsule = await self.repository.get_capsule_by_id(capsule_id=capsule_id)
        CapsulePolicy.can_interact(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
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
        CapsulePolicy.can_view(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
        content = await self.repository.get_content_by_id(content_id=content_id)
        content = ContentPolicy.can_interact(
            capsule_id=capsule_id,
            content_id=content_id,
            content=content,
            user_id=current_user.id,
        )
        download_url = await s3_client.generate_download_url(content.object_key)
        return UploadUrlResponseSchema(
            url=download_url,
            expires_in=settings.S3_LINK_EXPIRE_MINUTES * 60,
            object_key=content.object_key,
        )

    async def delete_content(
        self,
        capsule_id: int,
        content_id: int,
        current_user: CurrentUserSchema,
        s3_client: S3Client,
    ) -> None:
        capsule = await self.repository.get_capsule_by_id(capsule_id)
        CapsulePolicy.can_interact(
            capsule_id=capsule_id,
            capsule=capsule,
            user=current_user,
        )
        content = await self.repository.get_content_by_id(content_id)
        content = ContentPolicy.can_interact(
            capsule_id=capsule_id,
            content=content,
            content_id=content_id,
            user_id=current_user.id,
        )
        await self.repository.delete_content(
            content_id=content_id, capsule_id=capsule_id
        )
        await s3_client.delete_object(content.object_key)

    async def release_capsules(self, creator: CurrentUserSchema):
        capsules = await self.repository.get_capsules_by_creator_with_relations(
            creator_id=creator.id
        )
        for capsule in capsules:
            if capsule.send_at:
                self.scheduler.add_job(
                    func=self._send_capsule_to_users,
                    trigger="date",
                    run_date=capsule.send_at,
                    args=[capsule, creator.first_name],
                    id=f"capsule-{capsule.id}",
                    replace_existing=True,
                )
            else:
                CapsuleService._send_capsule_to_users(
                    capsule=capsule, creator_name=creator.first_name
                )

    @staticmethod
    def _send_capsule_to_users(capsule: CapsuleSchema, creator_name: str):
        for user in capsule.users:
            send_user_capsule_email_task.send(
                to_email=user.email,
                user_name=creator_name,
                capsule_name=capsule.title,
            )

    @staticmethod
    def get_allowed_extensions() -> set[str]:
        return ALLOWED_EXTENSIONS
