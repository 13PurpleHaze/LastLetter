from config import settings
from datetime import datetime, timedelta, timezone
from core.constants import RoleId
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
from modules.user.factories import CurrentUserSchemaFactory
from modules.user.schemas import CurrentUserSchema, UserUpdateSchema


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def register(self, user_register: UserRegisterSchema) -> CurrentUserSchema:
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

        send_verification_link_email_task.send(
            to_email=str(user.email),
            link=verification_link,
        )

        return CurrentUserSchemaFactory.user_schema_to_current_user_schema(user=user)

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
        current_user = AuthSchemaFactory.user_schema_to_current_user_schema(
            user=user_by_email
        )
        return AuthService.create_auth_tokens(current_user=current_user)

    async def verify_email(self, token: str):
        try:
            decoded = decode_jwt(token)
        except Exception:
            raise UnauthorizedError()

        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError(email=str(user_id))
        await self.user_service.update_user(
            user_id=user.id, user_update=UserUpdateSchema(email_verified=True)
        )

    async def resend_verification_link(self, user_verify: UserVerifySchema):
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_verify.email)
        )
        if (
            user_by_email
            and user_by_email.is_active
            and not user_by_email.email_verified
        ):
            link = AuthService.create_verification_link(user_id=user_by_email.id)
            send_verification_link_email_task.send(
                to_email=str(user_by_email.email),
                link=link,
            )

    async def reset_password_call(self, email: str):
        user_by_email = await self.user_service.get_user_by_email(email=email)
        if user_by_email and user_by_email.is_active:
            link = AuthService.create_password_reset_link(user_id=user_by_email.id)
            send_password_reset_email_task.send(link=link, to_email=email)

    async def confirm_reset_password(self, token: str, new_password: str):
        try:
            decoded = decode_jwt(token)
        except Exception:
            raise UnauthorizedError()
        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError(email=str(user_id))
        if not user.is_active:
            raise UserInactiveError(email=str(user_id))
        hashed_password = hash_password(new_password)
        await self.user_service.update_user(
            user_update=UserUpdateSchema(password=hashed_password), user_id=user_id
        )

    @staticmethod
    def refresh(current_user: CurrentUserSchema):
        return AuthService.create_auth_tokens(current_user=current_user)

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
    def create_auth_tokens(current_user: CurrentUserSchema) -> TokenSchema:
        payload = {
            "sub": str(current_user.id),
            "roles": [role.slug for role in current_user.roles],
            "iat": datetime.now(timezone.utc),
        }

        access_payload = {
            **payload,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        refresh_payload = {
            **payload,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
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
