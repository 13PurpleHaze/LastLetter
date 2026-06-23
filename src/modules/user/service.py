from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from config import settings
from core.constants import RoleSlug
from infrastructure.filter import Filter
from utils.auth.jwt import encode_jwt, decode_jwt
from utils.auth.secure import hash_password
from .exceptions import UserNotFoundError, UserInactiveError, EmailNotVerifiedError
from .repository import UserRepository
from .schemas import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    CurrentUserSchema,
)
from datetime import datetime, timedelta, timezone

from ..auth.exceptions import UnauthorizedError
from ..email.tasks import send_user_invite_verification_email_task


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_users(
        self,
        filter: Filter,
        pagination: PaginationParams,
    ) -> tuple[list[CurrentUserSchema], PageMetaSchema]:
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
    ) -> tuple[list[CurrentUserSchema], PageMetaSchema]:
        users, total = await self.repository.get_users_for_verify(
            current_user=current_user, limit=pagination.limit, offset=pagination.offset
        )
        return users, PageMetaSchema(
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def invite_attempt(
        self, role: str, user_id: int, current_user: CurrentUserSchema
    ):
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        if not user.is_active:
            raise UserInactiveError(email=user.email)
        if not user.email_verified:
            raise EmailNotVerifiedError(email=user.email)
        link = UserService.create_confirm_invite_link(
            user_id=user.id, current_user=current_user, role=role
        )
        send_user_invite_verification_email_task.send(
            to_email=user.email,
            from_email=current_user.email,
            link=link,
        )

    async def confirm_invite(self, token: str):
        try:
            decoded = decode_jwt(token)
        except Exception:
            raise UnauthorizedError()

        user_id = int(decoded["sub"])
        user = await self.repository.get_user_by_id(user_id)
        inviter_id = int(decoded["inviterId"])
        role = decoded["role"]
        if user:
            if role not in [role.slug for role in user.roles]:
                await self.repository.add_roles_to_user(
                    user_id=user_id, roles=[str(role)]
                )
            if role == RoleSlug.VERIFIER:
                await self.repository.update_user(
                    user_id=inviter_id,
                    user_update=UserUpdateSchema(verificator_id=user_id),
                )
            if role == RoleSlug.CHILD:
                await self.repository.invite_user(
                    user_id=user_id, inviter_id=inviter_id
                )

    async def create_user(
        self, user_create: UserCreateSchema, roles: list[str]
    ) -> UserSchema:
        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password
        return await self.repository.create_user(user_create=user_create, roles=roles)

    async def get_user_by_email(self, email: str) -> UserSchema | None:
        return await self.repository.get_user_by_email(email)

    async def get_user_by_id(self, user_id: int) -> UserSchema | None:
        return await self.repository.get_user_by_id(user_id)

    async def update_user(
        self, user_id: int, user_update: UserUpdateSchema
    ) -> UserSchema | None:
        return await self.repository.update_user(
            user_id=user_id, user_update=user_update
        )

    @staticmethod
    def create_confirm_invite_link(
        user_id: int, current_user: CurrentUserSchema, role: str
    ) -> str:
        payload = {
            "sub": str(user_id),
            "inviterId": str(current_user.id),
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        token = encode_jwt(
            payload=payload,
        )
        # Тут на фронтенд ссылка
        return f"{settings.BASE_URL}/users/confirm-invite?token={token}"
