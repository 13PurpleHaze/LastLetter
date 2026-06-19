from core.app_exception import AppException


class UserNotFoundError(AppException):
    def __init__(self, email: str | None = None):
        self.email = email
        if not email:
            super().__init__("Пользователь не найден")
        else:
            super().__init__(f"Пользователь с email {email} не найден")


class EmailNotVerifiedError(AppException):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} не подтвержден")


class EmailAlreadyVerifiedError(AppException):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} уже подтвержден")


class UserAlreadyExistsError(AppException):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Пользователь с email {email} уже существует")


class UserInactiveError(AppException):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Пользователь с email {email} заблокирован")
