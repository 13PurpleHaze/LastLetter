from core.app_exception import AppException


class InvalidCredentialsError(AppException):
    def __init__(self):
        super().__init__("Неверные email или пароль")


class UnauthorizedError(AppException):
    def __init__(self):
        super().__init__("Unauthorized")
