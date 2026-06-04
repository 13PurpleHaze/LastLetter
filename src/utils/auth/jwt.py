import jwt
from datetime import datetime, timedelta

from config import settings


def encode_jwt(
    payload: dict,
    private_key: str = settings.PRIVATE_KEY_PATH.read_text(),
    algorithm: str = settings.ALGORITHM,
    expire_in_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
):
    to_encode = payload.copy()
    exp = datetime.now() + timedelta(minutes=expire_in_minutes)
    to_encode.update({"exp": exp, "iat": datetime.now()})
    encoded = jwt.encode(
        algorithm=algorithm,
        payload=payload,
        key=private_key,
    )
    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.PUBLIC_KEY_PATH.read_text(),
    algorithm: str = settings.ALGORITHM,
) -> dict:
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
    )
    return decoded
