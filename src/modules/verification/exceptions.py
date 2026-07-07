from core.app_exception import AppException


class InvalidVerificator(AppException):
    def __init__(self, verificator_id: int, user_id: int):
        self.verificator_id = verificator_id
        self.user_id = user_id
        super().__init__(
            f"Пользователь с id {verificator_id} не является верификатором для пользователя с id {user_id}"
        )
