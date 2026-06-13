class UserNotFoundError(Exception):
    def __init__(self, email: str | None = None):
        self.email = email
        if not email:
            super().__init__("Пользователь не найден")
        else:
            super().__init__(f"Пользователь с email {email} не найден")


class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Неверные email или пароль")


class EmailNotVerifiedError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} не подтвержден")


class UserAlreadyExistsError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Пользователь с email {email} уже существует")


class UserInactiveError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Пользователь с email {email} заблокирован")
