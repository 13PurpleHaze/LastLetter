from datetime import datetime, timedelta, timezone
from config import settings
from modules.auth.exceptions import InvalidTokenError
from modules.auth.schemas import TokenSchema
from utils.auth.jwt import encode_jwt, decode_jwt


class TokenService:
    @staticmethod
    def create_auth_tokens(user_id: int) -> TokenSchema:
        payload = {
            "sub": str(user_id),
            "iat": datetime.now(timezone.utc),
        }

        access_token = encode_jwt(
            {
                **payload,
                "exp": datetime.now(timezone.utc)
                + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            }
        )

        refresh_token = encode_jwt(
            {
                **payload,
                "exp": datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            }
        )

        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )

    @staticmethod
    def create_verification_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.VERIFICATION_TOKEN_EXPIRES_DAYS * 24 * 60),
            "iat": datetime.now(timezone.utc),
        }
        return encode_jwt(payload=payload)

    @staticmethod
    def create_reset_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        return encode_jwt(payload=payload)

    @staticmethod
    def create_invite_token(user_id: int, inviter_id: int, role: str) -> str:
        payload = {
            "sub": str(user_id),
            "inviterId": str(inviter_id),
            "role": role,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.INVITE_TOKEN_EXPIRE_MINUTES * 24 * 60),
            "iat": datetime.now(timezone.utc),
        }
        return encode_jwt(payload=payload)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return decode_jwt(token)
        except Exception:
            raise InvalidTokenError()
