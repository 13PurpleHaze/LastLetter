from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from modules.capsules.exceptions import PermissionDeniedError
from modules.user.exceptions import (
    UserNotFoundError,
    UserInactiveError,
    EmailNotVerifiedError,
)
from modules.user.factories import CurrentUserSchemaFactory
from modules.user.schemas import (
    CurrentUserSchema,
    UserUpdateSchema,
)
from modules.user.service import UserService


class VerificationService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def get_users(
        self, pagination: PaginationParams, current_user: CurrentUserSchema
    ) -> tuple[list[CurrentUserSchema], PageMetaSchema]:
        users, meta = await self.user_service.get_users_for_verify(
            pagination=pagination, current_user=current_user
        )
        return users, meta

    async def verify_death(
        self, user_id: int, current_user: CurrentUserSchema
    ) -> CurrentUserSchema:
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        if not user.is_active:
            raise UserInactiveError(email=user.email)
        if not user.email_verified:
            raise EmailNotVerifiedError(email=user.email)
        if user.verificator_id != current_user.id:
            raise PermissionDeniedError()
        user_update = UserUpdateSchema(is_deceased=True)
        updated_user = await self.user_service.update_user(
            user_id=user.id, user_update=user_update
        )
        # TODO: cringe
        if not updated_user:
            return current_user
        return CurrentUserSchemaFactory.user_schema_to_current_user_schema(
            user=updated_user
        )
