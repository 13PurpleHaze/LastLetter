from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status

from api.v1.schemas.failed_response import FailedResponseSchema
from api.v1.schemas.pagination import PaginationParams, ListResponseSchema
from api.v1.schemas.success_response import SuccessResponseSchema
from core.constants import RoleSlug
from modules.auth.dependencies import get_current_user_with_roles
from modules.user.dependencies import get_user_service, get_user_filter
from modules.user.schemas import CurrentUserSchema, UserFilterSchema
from modules.user.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    path="/",
    description="Получить список пользователей",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {
            "model": SuccessResponseSchema[ListResponseSchema[CurrentUserSchema]]
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
        get_current_user_with_roles([RoleSlug.PARENT, RoleSlug.ADMIN])
    ),
):
    filter = get_user_filter(user_filter=user_filter)
    users, meta = await user_service.get_users(
        filter=filter,
        pagination=pagination,
    )
    return SuccessResponseSchema(result=ListResponseSchema(meta=meta, items=users))


@router.post(
    path="/{user_id}/invite",
    description="Добавить пользователя как верификатора или ребенка",
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
        get_current_user_with_roles([RoleSlug.PARENT, RoleSlug.ADMIN])
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
    description="Подтвердить инвайт как ребенка или верификатора для родителя",
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
        get_current_user_with_roles([RoleSlug.PARENT, RoleSlug.ADMIN])
    ),
):
    await user_service.confirm_invite(token=token)
    return SuccessResponseSchema(message="Успешный инвайт")
