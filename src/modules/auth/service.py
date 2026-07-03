from config import settings
from datetime import datetime, timedelta, timezone
from core.constants import RoleSlug
from modules.email.tasks import (
    send_password_reset_email_task,
    send_verification_link_email_task,
)
from utils.auth.jwt import encode_jwt, decode_jwt
from utils.auth.secure import check_password, hash_password
from .exceptions import (
    InvalidCredentialsError,
    UnauthorizedError,
)
from .schemas import UserRegisterSchema, TokenSchema, UserLoginSchema, UserVerifySchema
from modules.user.service import UserService
from .factory import AuthSchemaFactory
from modules.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    EmailNotVerifiedError,
    UserInactiveError,
)
from modules.user.schemas import (
    CurrentUserSchema,
    UserLightSchema,
    UserUpdateInternalSchema,
)


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def register(self, user_register: UserRegisterSchema) -> UserLightSchema:
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_register.email)
        )
        if user_by_email:
            raise UserAlreadyExistsError(email=str(user_by_email.email))

        user_create = AuthSchemaFactory.user_register_schema_to_user_create_schema(
            user=user_register
        )
        roles = AuthService.get_roles(user=user_register)
        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password
        user = await self.user_service.create_user(user_create=user_create, roles=roles)
        verification_link = AuthService.create_verification_link(user_id=user.id)

        send_verification_link_email_task.send(
            to_email=str(user.email),
            link=verification_link,
        )
        return user

    async def login(self, user_login: UserLoginSchema) -> TokenSchema:
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_login.email)
        )
        if not user_by_email:
            raise InvalidCredentialsError()
        if not user_by_email.email_verified:
            raise EmailNotVerifiedError(email=str(user_login.email))
        if not user_by_email.is_active:
            raise UserInactiveError(email=str(user_login.email))
        if not check_password(
            hashed_password=user_by_email.password, password=user_login.password
        ):
            raise InvalidCredentialsError()
        return AuthService.create_auth_tokens(user_id=user_by_email.id)

    async def verify_email(self, token: str):
        try:
            decoded = decode_jwt(token)
        except Exception:
            raise UnauthorizedError()

        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_with_roles_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError()
        if not user.is_active:
            raise UserInactiveError(email=str(user.email))
        await self.user_service.update_user(
            user_id=user_id,
            user_update=UserUpdateInternalSchema(email_verified=True),
            current_user=user,
        )

    async def resend_verification_link(self, user_verify: UserVerifySchema):
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_verify.email)
        )
        if not user_by_email:
            raise UserNotFoundError()
        if not user_by_email.is_active:
            raise UserInactiveError(email=str(user_by_email.email))
        if not user_by_email.email_verified:
            link = AuthService.create_verification_link(user_id=user_by_email.id)
            send_verification_link_email_task.send(
                to_email=str(user_by_email.email),
                link=link,
            )

    async def reset_password_call(self, email: str):
        user_by_email = await self.user_service.get_user_by_email(email=email)
        if not user_by_email:
            raise UserNotFoundError()
        if not user_by_email.is_active:
            raise UserInactiveError(email=str(user_by_email.email))

        link = AuthService.create_password_reset_link(user_id=user_by_email.id)
        send_password_reset_email_task.send(link=link, to_email=email)

    async def confirm_reset_password(self, token: str, new_password: str):
        try:
            decoded = decode_jwt(token)
        except Exception:
            raise UnauthorizedError()
        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_with_roles_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError()
        if not user.is_active:
            raise UserInactiveError(email=str(user.email))
        if not user.email_verified:
            raise EmailNotVerifiedError(email=str(user.email))
        hashed_password = hash_password(new_password)
        await self.user_service.update_user(
            user_update=UserUpdateInternalSchema(password=hashed_password),
            user_id=user_id,
            current_user=user,
        )

    @staticmethod
    def refresh(current_user: CurrentUserSchema):
        return AuthService.create_auth_tokens(user_id=current_user.id)

    @staticmethod
    def create_password_reset_link(user_id: int):
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        token = encode_jwt(
            payload=payload,
        )
        # Генериться ссылка на фронтенд(не на наш эндпоинт)
        password_reset_link = (
            f"{settings.BASE_URL}/password-reset-confirm?token={token}"
        )
        return password_reset_link

    @staticmethod
    def create_verification_link(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        token = encode_jwt(
            payload=payload,
            expire_in_minutes=settings.VERIFICATION_TOKEN_EXPIRES_DAYS * 24 * 60,
        )
        verification_link = (
            f"{settings.BASE_URL}/api/v1/auth/verify-email?token={token}"
        )
        return verification_link

    @staticmethod
    def create_auth_tokens(user_id: int) -> TokenSchema:
        payload = {
            "sub": str(user_id),
            "iat": datetime.now(timezone.utc),
        }

        access_payload = {
            **payload,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        refresh_payload = {
            **payload,
            "exp": datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }

        access_token = encode_jwt(payload=access_payload)
        refresh_token = encode_jwt(
            payload=refresh_payload,
            expire_in_minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60,
        )
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )

    @staticmethod
    def get_roles(user) -> list[str]:
        return [
            role.value
            for role, flag in [
                (RoleSlug.PARENT, user.is_parent),
                (RoleSlug.CHILD, user.is_child),
                (RoleSlug.VERIFIER, user.is_verifier),
            ]
            if flag
        ]
