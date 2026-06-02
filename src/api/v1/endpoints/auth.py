from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    path="/register",
    description="Зарегистрировать пользователя",
)
async def register():
    pass


@router.get(
    path="/verify-email",
    description="Подтвердить email (переход по ссылке из письма)",
)
async def verify_email():
    pass


@router.post(
    path="/resend-verification",
    description="Повторно отправить письмо с подтверждением",
)
async def resend_verification():
    pass


@router.post(
    path="/login",
    description="Залогинить пользователя",
)
async def login():
    pass


@router.post(
    path="/refresh",
    description="Обновить токен доступа",
)
async def refresh():
    pass


@router.get(
    path="/logout",
    description="Разлогинить пользователя",
)
async def logout():
    pass


@router.post(path="/reset-password", description="Запросить сброс пароля")
async def reset_password():
    pass


@router.post(
    path="/reset-password-confirm",
    description="Подтвердить сброс пароля (установить новый)",
)
async def reset_password_confirm():
    pass


@router.post(
    path="/change-password",
    description="Сменить пароль (для авторизованных)",
)
async def change_password():
    pass


@router.get(
    path="/me",
    description="Получить текущего пользователя",
)
async def get_me():
    pass
