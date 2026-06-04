from config import settings
from datetime import datetime, timedelta, timezone
from constants import RoleId
from utils.auth.jwt import encode_jwt, decode_jwt
from utils.auth.secure import check_password
from .exception import (
    InvalidCredentialsError,
    EmailNotVerifiedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserInactiveError,
)
from .schemas import UserRegisterSchema, TokenSchema, UserLoginSchema, UserVerifySchema
from modules.user.service import UserService
from .factory import AuthSchemaFactory
from ..user.schemas import UserSchema, CurrentUserSchema


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def register(
        self, user_register: UserRegisterSchema
    ) -> tuple[UserSchema, str]:
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_register.email)
        )
        if user_by_email:
            raise UserAlreadyExistsError(email=user_by_email.email)

        user_create = AuthSchemaFactory.user_register_schema_to_user_create_schema(
            user=user_register
        )
        role_ids = AuthService.get_role_ids(user=user_register)
        user = await self.user_service.create_user(
            user_create=user_create, role_ids=role_ids
        )
        verification_link = AuthService.create_verification_link(user_id=user.id)
        return user, verification_link

    async def login(self, user_login: UserLoginSchema) -> TokenSchema:
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_login.email)
        )
        if not user_by_email:
            raise UserNotFoundError(email=str(user_login.email))
        if not user_by_email.email_verified:
            raise EmailNotVerifiedError(email=str(user_login.email))
        if not user_by_email.is_active:
            raise UserInactiveError(email=str(user_login.email))
        if not check_password(
            hashed_password=user_by_email.password, password=user_login.password
        ):
            raise InvalidCredentialsError()
        current_user = AuthSchemaFactory.user_schema_to_current_user_schema(
            user=user_by_email
        )
        return AuthService.create_auth_tokens(current_user=current_user)

    async def verify_email(self, token: str) -> None:
        decoded = decode_jwt(token)
        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError(email=str(user_id))
        await self.user_service.verify_email(user_id=user.id)

    async def resend_verification_link(self, user_verify: UserVerifySchema) -> str:
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_verify.email)
        )
        if not user_by_email:
            raise UserNotFoundError(email=str(user_verify.email))
        if not user_by_email.is_active:
            raise UserInactiveError(email=str(user_verify.email))
        return AuthService.create_verification_link(user_id=user_by_email.id)

    @staticmethod
    def refresh(current_user: CurrentUserSchema):
        return AuthService.create_auth_tokens(current_user=current_user)

    @staticmethod
    def create_verification_link(user_id: int) -> str:
        # Тихо не спеша генерим токен
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        token = encode_jwt(
            payload=payload,
            expire_in_minutes=settings.VERIFICATION_TOKEN_EXPIRES_DAYS * 24 * 60,
        )
        # Тут плохо maxic-string, нужно вынести протокол и остальное тоже в константы
        verification_link = f"http://{settings.HOST_NAME}:{settings.PORT}/api/v1/auth/verify-email?token={token}"
        return verification_link

    @staticmethod
    def create_auth_tokens(current_user: CurrentUserSchema) -> TokenSchema:
        payload = {
            "sub": str(current_user.id),
            "roles": [role.slug for role in current_user.roles],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }

        access_token = encode_jwt(payload=payload)
        refresh_token = encode_jwt(
            payload=payload,
            expire_in_minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60,
        )
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )

    # Лучше собирать не id'шники, а названия и по ним уже в репозитории делать запрос
    @staticmethod
    def get_role_ids(user) -> list[int]:
        return [
            role_id.value
            for role_id, flag in [
                (RoleId.PARENT, user.is_parent),
                (RoleId.CHILD, user.is_child),
                (RoleId.VERIFIER, user.is_verifier),
            ]
            if flag
        ]
