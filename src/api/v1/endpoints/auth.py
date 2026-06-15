from fastapi import APIRouter, Depends, status

from api.v1.schemas.failed_response import FailedResponseSchema
from api.v1.schemas.success_response import SuccessResponseSchema
from modules.auth.dependencies import get_auth_service, get_current_active_user
from modules.auth.schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    UserVerifySchema,
    TokenSchema,
    UserPasswordConfirmSchema,
)
from modules.auth.service import AuthService
from modules.user.schemas import CurrentUserSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    path="/register",
    description="Зарегистрировать пользователя",
    response_model=SuccessResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": SuccessResponseSchema[CurrentUserSchema]},
        status.HTTP_409_CONFLICT: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def register(
    user: UserRegisterSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    created_user = await auth_service.register(user_register=user)
    return SuccessResponseSchema(result=created_user)


@router.get(
    path="/verify-email",
    description="Подтвердить email (переход по ссылке из письма)",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.verify_email(token=token)
    return SuccessResponseSchema(message="Ваш email подтвержден")


@router.post(
    path="/resend-verification",
    description="Повторно отправить письмо с подтверждением",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[CurrentUserSchema]},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def resend_verification(
    user_verify: UserVerifySchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.resend_verification_link(user_verify=user_verify)
    return SuccessResponseSchema(
        message=f"Ссылка на подтверждение email отправлена по адресу {user_verify.email}"
    )


@router.post(
    path="/login",
    description="Залогинить пользователя",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[TokenSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def login(
    user: UserLoginSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.login(user_login=user)
    return SuccessResponseSchema(result=tokens)


@router.post(
    path="/refresh",
    description="Обновить токен доступа",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[TokenSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def refresh(
    user: CurrentUserSchema = Depends(get_current_active_user),
):
    tokens = AuthService.refresh(current_user=user)
    return SuccessResponseSchema(result=tokens)


@router.post(
    path="/reset-password",
    description="Запросить сброс пароля",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def reset_password(
    user_verify: UserVerifySchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.reset_password_call(email=str(user_verify.email))
    return SuccessResponseSchema(
        message=f"Ссылка на сброс пароля отправлена по адресу {user_verify.email}"
    )


@router.post(
    path="/reset-password-confirm",
    description="Подтвердить сброс пароля (установить новый)",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[CurrentUserSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def reset_password_confirm(
    token: str,
    password_confirm: UserPasswordConfirmSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.confirm_reset_password(
        token=token, new_password=password_confirm.password
    )
    return SuccessResponseSchema(message="Успешный сброс пароля")


@router.get(
    path="/me",
    description="Получить текущего пользователя",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_me(
    user: CurrentUserSchema = Depends(get_current_active_user),
):
    return SuccessResponseSchema(result=user)
