from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from core.constants import RoleSlug
from infrastructure.filter import Filter
from utils.auth.link import create_link_with_token
from modules.auth.services.token_service import TokenService
from modules.email.tasks import send_user_invite_verification_email_task
from .exceptions import UserNotFoundError
from .policy import UserPolicy
from .repository import UserRepository
from .schemas import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    CurrentUserSchema,
    UserLightSchema,
    UserAuthSchema,
    UserUpdateInternalSchema,
)


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_users(
        self,
        filter: Filter,
        pagination: PaginationParams,
    ) -> tuple[list[UserLightSchema], PageMetaSchema]:
        users, total = await self.repository.get_users(
            filter=filter,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PageMetaSchema(
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        return users, meta

    async def get_users_for_verify(
        self, pagination: PaginationParams, current_user: CurrentUserSchema
    ) -> tuple[list[UserLightSchema], PageMetaSchema]:
        users, total = await self.repository.get_users_for_verify(
            current_user_id=current_user.id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        return users, PageMetaSchema(
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def invite_attempt(
        self, role: str, user_id: int, current_user: CurrentUserSchema
    ):
        user = await self.repository.get_user_with_roles_by_id(user_id=user_id)
        user = UserPolicy.can_interact(user=user)
        token = TokenService.create_invite_token(
            user_id=user_id, role=role, inviter_id=current_user.id
        )
        link = create_link_with_token(path="/users/confirm-invite", token=token)
        send_user_invite_verification_email_task.send(
            to_email=user.email,
            from_email=current_user.email,
            link=link,
        )

    async def confirm_invite(self, token: str):
        decoded = TokenService.decode_token(token)
        user_id = int(decoded["sub"])
        user = await self.repository.get_user_with_roles_by_id(user_id=user_id)
        inviter_id = int(decoded["inviterId"])
        role = decoded["role"]
        user = UserPolicy.can_interact(user=user)

        if not any(role == r.slug for r in user.roles):
            await self.repository.add_roles_to_user(user_id=user_id, roles=[str(role)])
        if role == RoleSlug.VERIFIER:
            await self.repository.update_user(
                user_id=inviter_id,
                user_update=UserUpdateInternalSchema(verificator_id=user_id),
            )
        if role == RoleSlug.CHILD:
            await self.repository.invite_user(user_id=user_id, inviter_id=inviter_id)

    async def create_user(
        self, user_create: UserCreateSchema, roles: list[str]
    ) -> UserLightSchema:
        return await self.repository.create_user(user_create=user_create, roles=roles)

    async def get_user_by_email(self, email: str) -> UserAuthSchema | None:
        return await self.repository.get_user_by_email(email)

    async def get_user_by_id(self, user_id: int) -> UserSchema | None:
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user

    async def get_user_with_roles_by_id(self, user_id: int) -> CurrentUserSchema | None:
        return await self.repository.get_user_with_roles_by_id(user_id)

    async def update_user(
        self,
        user_id: int,
        current_user: CurrentUserSchema,
        user_update: UserUpdateSchema,
    ) -> UserSchema | None:
        user = await self.repository.get_user_with_roles_by_id(user_id=user_id)
        UserPolicy.can_update(user=user, current_user=current_user)
        return await self.repository.update_user(
            user_id=user_id, user_update=user_update
        )

    async def mark_as_deceased(self, user: CurrentUserSchema) -> UserSchema | None:
        user_update = UserUpdateInternalSchema(is_deceased=True)
        return await self.repository.update_user(
            user_id=user.id, user_update=user_update
        )
