from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status

from api.v1.schemas.failed_response import FailedResponseSchema
from api.v1.schemas.pagination import PaginationParams, ListResponseSchema
from api.v1.schemas.success_response import SuccessResponseSchema
from core.constants import RoleSlug
from modules.auth.dependencies import get_current_user_with_roles
from modules.user.dependencies import get_user_service, get_user_filter
from modules.user.schemas import (
    CurrentUserSchema,
    UserFilterSchema,
    UserLightSchema,
    UserSchema,
    UserUpdateSchema,
)
from modules.user.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    path="",
    description="Получить список пользователей",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {
            "model": SuccessResponseSchema[ListResponseSchema[UserLightSchema]]
        },
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_users(
    pagination: Annotated[PaginationParams, Depends()],
    user_filter: Annotated[UserFilterSchema, Depends()],
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles(
            [RoleSlug.PARENT, RoleSlug.CHILD, RoleSlug.VERIFIER, RoleSlug.ADMIN]
        )
    ),
):
    filter = get_user_filter(user_filter=user_filter)
    users, meta = await user_service.get_users(
        filter=filter,
        pagination=pagination,
    )
    return SuccessResponseSchema(result=ListResponseSchema(meta=meta, items=users))


@router.patch(
    path="/{user_id}",
    description="Обновить не чувствительные данные профиля пользователя",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[UserSchema]},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def update_user(
    user_id: int,
    user: UserUpdateSchema,
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
):
    updated_user = await user_service.update_user(
        user_id=user_id, user_update=user, current_user=current_user
    )
    return SuccessResponseSchema(result=updated_user)


@router.post(
    path="/{user_id}/invite",
    description="Добавить пользователя как верификатора или ребенка. Связать пользователей короче",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def invite_attempt(
    user_id: int,
    role: Literal[RoleSlug.VERIFIER, RoleSlug.CHILD],
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
):
    await user_service.invite_attempt(
        user_id=user_id,
        current_user=current_user,
        role=role,
    )
    return SuccessResponseSchema(message="Сообщение отправлено пользователю на email")


@router.post(
    path="/confirm-invite",
    description="Подтвердить инвайт как ребенка или верификатора",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def confirm_invite(
    token: str,
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.CHILD, RoleSlug.VERIFIER])
    ),
):
    await user_service.confirm_invite(token=token)
    return SuccessResponseSchema(message="Успешный инвайт")
