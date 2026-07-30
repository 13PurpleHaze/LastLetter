from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from modules.auth.exceptions import InvalidCredentialsError
from modules.auth.services.token_service import TokenService
from modules.user.exceptions import UserInactiveError, UserInvalidRoleError
from modules.auth.services.auth_service import AuthService
from modules.user.dependencies import get_user_service
from modules.user.schemas import CurrentUserSchema
from modules.user.service import UserService


def get_auth_service(user_service: UserService = Depends(get_user_service)):
    return AuthService(user_service=user_service)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    user_service: UserService = Depends(get_user_service),
) -> CurrentUserSchema:
    decoded = TokenService.decode_token(creds.credentials)
    user_id = int(decoded["sub"])
    user = await user_service.get_user_with_roles_by_id(user_id=user_id)
    if not user:
        raise InvalidCredentialsError()
    return user


def get_current_active_user(
    user: CurrentUserSchema = Depends(get_current_user),
) -> CurrentUserSchema:
    if not user.is_active:
        raise UserInactiveError(email=user.email)
    return user


def get_current_user_with_roles(
    allowed_roles: list[str],
):
    def dependency(
        user: CurrentUserSchema = Depends(get_current_active_user),
    ) -> CurrentUserSchema:
        user_roles = [r.slug for r in user.roles]
        if not any(role in user_roles for role in allowed_roles):
            raise UserInvalidRoleError(email=user.email, roles=allowed_roles)
        return user

    return dependency
