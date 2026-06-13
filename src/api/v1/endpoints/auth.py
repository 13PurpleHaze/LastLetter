from fastapi import APIRouter, Depends, status, BackgroundTasks

from api.v1.schemas.failed_response import FailedResponseSchema
from api.v1.schemas.success_response import SuccessResponseSchema
from modules.auth.dependencies import get_auth_service, get_current_active_user
from modules.auth.schemas import UserRegisterSchema, UserLoginSchema, UserVerifySchema
from modules.auth.service import AuthService
from modules.email.service import EmailService
from modules.user.schemas import CurrentUserSchema

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    path="/register",
    description="Зарегистрировать пользователя",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_201_CREATED: {"model": SuccessResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def register(
    user: UserRegisterSchema,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    created_user, link = await auth_service.register(user_register=user)
    background_tasks.add_task(
        EmailService.send_email,
        to_email=created_user.email,
        title="Подтверждение email",
        text=f"Подтвердите email перейдя по этой ссылке {link}",
    )
    return SuccessResponseSchema(result=[])


@router.get(
    path="/verify-email",
    description="Подтвердить email (переход по ссылке из письма)",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.verify_email(token=token)
    return SuccessResponseSchema(result=[])


@router.post(
    path="/resend-verification",
    description="Повторно отправить письмо с подтверждением",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def resend_verification(
    user: UserVerifySchema,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    link = auth_service.resend_verification_link(user_verify=user)
    background_tasks.add_task(
        EmailService.send_email,
        to_email=str(user.email),
        title="Подтверждение email",
        text=f"Подтвердите email перейдя по этой ссылке {link}",
    )
    return SuccessResponseSchema(result=[])


@router.post(
    path="/login",
    description="Залогинить пользователя",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
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
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def refresh(
    user: CurrentUserSchema = Depends(get_current_active_user),
):
    tokens = AuthService.refresh(current_user=user)
    return SuccessResponseSchema(result=tokens)


# Разлогинивать можно только если на стороне сервера есть механизм блеклистов для токенов
@router.get(
    path="/logout",
    description="Разлогинить пользователя",
)
async def logout():
    pass


# Логика сброса примерно такая - пользователь дергает эту ручку
# Ему отправляется email
# Он переходит по email передает на некст ручку токен, его проверяем - если все ок, то меняем пароль и разлогиниваем всех пользователей
# Тут тоже нужны блек листы чтобы пользователи с refresh-token и старым паролем не могли по кд обновляться и иметь доступ
@router.post(path="/reset-password", description="Запросить сброс пароля")
async def reset_password():
    pass


@router.post(
    path="/reset-password-confirm",
    description="Подтвердить сброс пароля (установить новый)",
)
async def reset_password_confirm():
    pass


@router.get(
    path="/me",
    description="Получить текущего пользователя",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_me(
    user: CurrentUserSchema = Depends(get_current_active_user),
):
    return SuccessResponseSchema(result=user)
