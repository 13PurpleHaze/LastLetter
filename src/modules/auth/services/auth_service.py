from core.constants import RoleSlug
from modules.auth.services.token_service import TokenService
from modules.email.tasks import (
    send_password_reset_email_task,
    send_verification_link_email_task,
)
from utils.auth.link import create_link_with_token
from utils.auth.secure import check_password, hash_password
from modules.auth.exceptions import (
    InvalidCredentialsError,
)
from modules.auth.schemas import (
    UserRegisterSchema,
    TokenSchema,
    UserLoginSchema,
    UserVerifySchema,
)
from modules.user.service import UserService
from modules.auth.factory import AuthSchemaFactory
from modules.user.exceptions import (
    UserAlreadyExistsError,
)
from modules.user.schemas import (
    CurrentUserSchema,
    UserLightSchema,
    UserUpdateInternalSchema,
)
from modules.user.policy import UserPolicy


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
        token = TokenService.create_verification_token(user_id=user.id)
        link = create_link_with_token(path="/api/v1/auth/verify-email", token=token)
        send_verification_link_email_task.send(
            to_email=str(user.email),
            link=link,
        )
        return user

    async def login(self, user_login: UserLoginSchema) -> TokenSchema:
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_login.email)
        )
        user = UserPolicy.can_login(user=user_by_email)
        if not check_password(
            hashed_password=user.password, password=user_login.password
        ):
            raise InvalidCredentialsError()
        return TokenService.create_auth_tokens(user_id=user.id)

    async def verify_email(self, token: str):
        decoded = TokenService.decode_token(token)
        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_with_roles_by_id(user_id=user_id)
        user = UserPolicy.can_verify_email(user=user)
        await self.user_service.update_user(
            user_id=user_id,
            current_user=user,
            user_update=UserUpdateInternalSchema(email_verified=True),
        )

    async def resend_verification_link(self, user_verify: UserVerifySchema):
        user_by_email = await self.user_service.get_user_by_email(
            email=str(user_verify.email)
        )
        user = UserPolicy.can_verify_email(user=user_by_email)
        if not user.email_verified:
            token = TokenService.create_verification_token(user_id=user.id)
            link = create_link_with_token(path="/api/v1/auth/verify-email", token=token)
            send_verification_link_email_task.send(
                to_email=str(user.email),
                link=link,
            )

    async def reset_password_call(self, email: str):
        user_by_email = await self.user_service.get_user_by_email(email=email)
        user = UserPolicy.can_interact(user=user_by_email)
        token = TokenService.create_reset_token(user_id=user.id)
        link = create_link_with_token(path="/api/v1/auth/reset-password", token=token)
        send_password_reset_email_task.send(link=link, to_email=email)

    async def confirm_reset_password(self, token: str, new_password: str):
        decoded = TokenService.decode_token(token)
        user_id = int(decoded["sub"])
        user = await self.user_service.get_user_with_roles_by_id(user_id=user_id)
        user = UserPolicy.can_interact(user=user)
        hashed_password = hash_password(new_password)
        await self.user_service.update_user(
            user_update=UserUpdateInternalSchema(password=hashed_password),
            user_id=user_id,
            current_user=user,
        )

    @staticmethod
    def refresh(current_user: CurrentUserSchema):
        return TokenService.create_auth_tokens(user_id=current_user.id)

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
