from core.app_exception import AppException


class CapsuleNotFoundError(AppException):
    def __init__(self, capsule_id: int):
        self.capsule_id = capsule_id
        super().__init__(f"Капсула с id {capsule_id} не найдена")


class ContentNotFoundError(AppException):
    def __init__(self, content_id: int):
        self.capsule_id = content_id
        super().__init__(f"Контент с id {content_id} не найден")


class ObjectNotFoundError(AppException):
    def __init__(self, object_key: str):
        self.object_key = object_key
        super().__init__(f"Объект с key {object_key} не найден, либо еще не загружен")


class CapsuleNotAccessibleError(AppException):
    def __init__(self, capsule_id: int, user_id: int):
        super().__init__(
            f"Пользователь {user_id} не имеет доступа к капсуле {capsule_id}"
        )


class CapsuleNotAllowAttachUser(AppException):
    def __init__(self, capsule_id: int, user_id: int):
        super().__init__(
            f"Пользователя {user_id} нельзя добавить к капсуле {capsule_id}"
        )


class CapsuleNotAllowedExtension(AppException):
    def __init__(self, ext: str):
        super().__init__(f"{ext} не поддерживается")
