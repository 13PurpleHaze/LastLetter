from core.app_exception import AppException


class InvalidCredentialsError(AppException):
    def __init__(self):
        super().__init__("Неверные email или пароль")


class InvalidTokenError(AppException):
    def __init__(self):
        super().__init__("Invalid token")
