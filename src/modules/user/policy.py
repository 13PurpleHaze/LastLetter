from typing import TypeVar

from core.constants import RoleSlug
from modules.auth.exceptions import InvalidCredentialsError
from modules.user.exceptions import (
    EmailNotVerifiedError,
    UserInactiveError,
    UserNotFoundError,
    EmailAlreadyVerifiedError,
    UserNotAllowedError,
    UserInvalidRoleError,
)
from modules.user.schemas import UserInternalSchema, CurrentUserSchema, UserAuthSchema
from modules.verification.exceptions import InvalidVerificator

T = TypeVar("T", bound=UserInternalSchema)


class UserPolicy:
    @staticmethod
    def _user_exists(user: T | None) -> T:
        if not user:
            raise UserNotFoundError()
        return user

    @staticmethod
    def _user_active(user: T) -> T:
        if not user.is_active:
            raise UserInactiveError(email=str(user.email))
        return user

    @staticmethod
    def _user_email_verified(user: T) -> T:
        if not user.email_verified:
            raise EmailNotVerifiedError(email=str(user.email))
        return user

    @staticmethod
    def can_interact(user: T | None) -> T:
        user_exists = UserPolicy._user_exists(user=user)
        UserPolicy._user_active(user=user_exists)
        UserPolicy._user_email_verified(user=user_exists)
        return user_exists

    @staticmethod
    def can_login(user: UserAuthSchema | None) -> UserAuthSchema:
        if not user:
            raise InvalidCredentialsError()
        UserPolicy._user_active(user=user)
        UserPolicy._user_email_verified(user=user)
        return user

    @staticmethod
    def can_update(
        user: CurrentUserSchema | None, current_user: CurrentUserSchema
    ) -> CurrentUserSchema:
        user_exists = UserPolicy._user_exists(user=user)
        UserPolicy._user_active(user=user_exists)
        if user_exists.id != current_user.id:
            raise UserNotAllowedError(email=str(current_user.email))
        return user_exists

    @staticmethod
    def can_verify_email(user: T | None) -> T:
        user_exists = UserPolicy._user_exists(user=user)
        UserPolicy._user_active(user=user_exists)
        if user_exists.email_verified:
            raise EmailAlreadyVerifiedError(email=str(user_exists.email))
        return user_exists

    @staticmethod
    def can_verify_death(
        user: CurrentUserSchema | None, verificator_id: int
    ) -> CurrentUserSchema:
        user_interact = UserPolicy.can_interact(user=user)

        if user_interact.verificator_id != verificator_id:
            raise InvalidVerificator(
                verificator_id=verificator_id, user_id=user_interact.id
            )
        if not any(role.slug == RoleSlug.PARENT for role in user_interact.roles):
            raise UserInvalidRoleError(
                email=str(user_interact.email), roles=[RoleSlug.PARENT.value]
            )
        return user_interact
