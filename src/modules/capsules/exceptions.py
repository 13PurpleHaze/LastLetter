from core.app_exception import AppException


class CapsuleNotFoundError(AppException):
    def __init__(self, capsule_id: int):
        self.capsule_id = capsule_id
        super().__init__(f"Капсула с id {capsule_id} не найдена")


class ContentNotFoundError(AppException):
    def __init__(self, content_id: int):
        self.capsule_id = content_id
        super().__init__(f"Контент с id {content_id} не найден")


# TODO: вынести отсюда в auth
class PermissionDeniedError(AppException):
    def __init__(self):
        super().__init__("Доступ запрещен")
