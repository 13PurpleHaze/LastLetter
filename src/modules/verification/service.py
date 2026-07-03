from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from core.constants import RoleSlug
from modules.capsules.exceptions import PermissionDeniedError
from modules.capsules.service import CapsuleService
from modules.user.exceptions import (
    UserNotFoundError,
    UserInactiveError,
    EmailNotVerifiedError,
)
from modules.user.schemas import (
    CurrentUserSchema,
    UserLightSchema,
    UserSchema,
)
from modules.user.service import UserService


class VerificationService:
    def __init__(self, user_service: UserService, capsule_service: CapsuleService):
        self.user_service = user_service
        self.capsule_service = capsule_service

    async def get_users(
        self, pagination: PaginationParams, current_user: CurrentUserSchema
    ) -> tuple[list[UserLightSchema], PageMetaSchema]:
        users, meta = await self.user_service.get_users_for_verify(
            pagination=pagination, current_user=current_user
        )
        return users, meta

    async def _get_valid_user(
        self, user_id: int, verificator_id: int
    ) -> CurrentUserSchema:
        user = await self.user_service.get_user_with_roles_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        if not user.is_active:
            raise UserInactiveError(email=str(user.email))
        if not user.email_verified:
            raise EmailNotVerifiedError(email=str(user.email))
        if user.verificator_id != verificator_id:
            raise PermissionDeniedError()
        if not any([role.slug == RoleSlug.PARENT for role in user.roles]):
            raise PermissionDeniedError()
        return user

    async def verify_death(
        self, user_id: int, current_user: CurrentUserSchema
    ) -> UserSchema | None:
        user = await self._get_valid_user(
            user_id=user_id, verificator_id=current_user.id
        )
        updated_user = await self.user_service.mark_as_deceased(user=user)

        await self.capsule_service.release_capsules(user)

        return updated_user
