from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from utils.auth.jwt import decode_jwt
from .service import AuthService
from modules.user.dependencies import get_user_service
from modules.user.schemas import CurrentUserSchema
from modules.user.service import UserService
from ..user.factories import CurrentUserSchemaFactory


def get_auth_service(user_service: UserService = Depends(get_user_service)):
    return AuthService(user_service=user_service)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    user_service: UserService = Depends(get_user_service),
) -> CurrentUserSchema:
    try:
        token = decode_jwt(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user_id = int(token["sub"])
    user = await user_service.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return CurrentUserSchemaFactory.user_schema_to_current_user_schema(user)


def get_current_active_user(
    user: CurrentUserSchema = Depends(get_current_user),
) -> CurrentUserSchema:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь заблокирован"
        )
    return user


def get_current_user_with_roles(
    allowed_roles: list[str],
):
    def dependency(
        user: CurrentUserSchema = Depends(get_current_active_user),
    ) -> CurrentUserSchema:
        user_roles = [r.slug for r in user.roles]
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required one of roles: {allowed_roles}",
            )
        return user

    return dependency
