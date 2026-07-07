from config import settings


def create_link_with_token(path: str, token: str) -> str:
    return f"{settings.BASE_URL}{path}?token={token}"
