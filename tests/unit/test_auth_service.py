import pytest
from datetime import date

from unittest.mock import Mock
from core.constants import RoleSlug
from modules.auth.exceptions import InvalidCredentialsError
from modules.auth.schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    TokenSchema,
    UserVerifySchema,
)
from modules.auth.services.auth_service import AuthService
from modules.user.exceptions import UserAlreadyExistsError
from modules.user.schemas import (
    UserLightSchema,
    UserCreateSchema,
    UserAuthSchema,
    CurrentUserSchema,
    RoleSchema,
    UserUpdateInternalSchema,
)
from modules.user.service import UserService


@pytest.mark.asyncio
async def test_register_success(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user_register = UserRegisterSchema(
        email="test@test.com",
        password="password123",
        first_name="test_first_name",
        date_of_birth=date(2000, 2, 21),
        is_parent=True,
        is_child=False,
        is_verifier=False,
    )
    created_user = UserLightSchema(
        id=1,
        email=user_register.email,
        first_name=user_register.first_name,
        is_deceased=False,
    )
    user_create = UserCreateSchema(
        email=user_register.email,
        first_name=user_register.first_name,
        date_of_birth=user_register.date_of_birth,
        password="123",
    )

    user_service.get_user_by_email.return_value = None
    user_service.create_user.return_value = created_user

    monkeypatch.setattr(
        "modules.auth.services.auth_service.AuthSchemaFactory.user_register_schema_to_user_create_schema",
        Mock(return_value=user_create),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.hash_password",
        Mock(return_value="hashed_password"),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.TokenService.create_verification_token",
        Mock(return_value="token"),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.create_link_with_token",
        Mock(return_value="verify-link"),
    )
    email_task = Mock()
    monkeypatch.setattr(
        "modules.auth.services.auth_service.send_verification_link_email_task",
        email_task,
    )
    # Act
    result = await auth_service.register(user_register=user_register)

    # Assert
    assert result == created_user
    assert user_create.password == "hashed_password"
    user_service.create_user.assert_called_once_with(
        user_create=user_create,
        roles=[RoleSlug.PARENT.value],
    )
    email_task.send.assert_called_once_with(
        to_email=user_register.email,
        link="verify-link",
    )


@pytest.mark.asyncio
async def test_register_fail(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user_register = UserRegisterSchema(
        email="test@test.com",
        password="password123",
        first_name="test_first_name",
        date_of_birth=date(2000, 2, 21),
        is_parent=True,
        is_child=False,
        is_verifier=False,
    )
    user_service.get_user_by_email.return_value = UserAuthSchema(
        id=1,
        email=user_register.email,
        email_verified=True,
        first_name=user_register.first_name,
        date_of_birth=user_register.date_of_birth,
        password="123",
        is_deceased=False,
        is_active=True,
    )
    # Act
    with pytest.raises(
        UserAlreadyExistsError,
        match=f"Пользователь с email {user_register.email} уже существует",
    ) as exc:
        await auth_service.register(user_register=user_register)

    # Assert
    user_service.get_user_by_email.assert_awaited_once_with(email=user_register.email)
    user_service.create_user.assert_not_awaited()
    assert exc.value.email == user_register.email


@pytest.mark.asyncio
async def test_login_success(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user_login = UserLoginSchema(
        email="lisa@mail.com",
        password="lisa123",
    )
    user_by_email = UserAuthSchema(
        id=1,
        email=user_login.email,
        email_verified=True,
        first_name="Temp",
        date_of_birth=date(2000, 2, 21),
        password="hashed_password",
        is_deceased=False,
        is_active=True,
    )
    expected_tokens = TokenSchema(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
    )
    user_service.get_user_by_email.return_value = user_by_email
    monkeypatch.setattr(
        "modules.auth.services.auth_service.UserPolicy.can_login",
        Mock(return_value=user_by_email),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.check_password",
        Mock(return_value=True),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.TokenService.create_auth_tokens",
        Mock(return_value=expected_tokens),
    )

    # Act
    result = await auth_service.login(user_login=user_login)

    # Assert
    assert result == expected_tokens
    user_service.get_user_by_email.assert_awaited_once_with(email=user_login.email)


@pytest.mark.asyncio
async def test_login_invalid_password(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user_login = UserLoginSchema(
        email="lisa@mail.com",
        password="lisa123",
    )
    user_by_email = UserAuthSchema(
        id=1,
        email=user_login.email,
        email_verified=True,
        first_name="Temp",
        date_of_birth=date(2000, 2, 21),
        password="hashed_password",
        is_deceased=False,
        is_active=True,
    )
    user_service.get_user_by_email.return_value = user_by_email
    monkeypatch.setattr(
        "modules.auth.services.auth_service.UserPolicy.can_login",
        Mock(return_value=user_by_email),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.check_password",
        Mock(return_value=False),
    )

    # Act
    with pytest.raises(InvalidCredentialsError, match="Неверные email или пароль"):
        await auth_service.login(user_login=user_login)

    # Assert
    user_service.get_user_by_email.assert_awaited_once_with(email=user_login.email)


@pytest.mark.asyncio
async def test_verify_email_success(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user = CurrentUserSchema(
        id=10,
        email="test@test.com",
        email_verified=False,
        first_name="Test",
        date_of_birth=date(2000, 2, 21),
        is_deceased=False,
        is_active=True,
        verificator_id=10,
        roles=[RoleSchema(id=1, slug=RoleSlug.PARENT, title="Parent")],
    )
    decoded = {"sub": 10}
    monkeypatch.setattr(
        "modules.auth.services.auth_service.TokenService.decode_token",
        Mock(return_value=decoded),
    )

    user_service.get_user_with_roles_by_id.return_value = user

    monkeypatch.setattr(
        "modules.auth.services.auth_service.UserPolicy.can_verify_email",
        Mock(return_value=user),
    )

    # Act
    await auth_service.verify_email(token="token")

    # Assert
    user_service.get_user_with_roles_by_id.assert_awaited_once_with(
        user_id=user.id,
    )
    user_service.update_user.assert_awaited_once_with(
        user_id=user.id,
        current_user=user,
        user_update=UserUpdateInternalSchema(email_verified=True),
    )


@pytest.mark.asyncio
async def test_resend_verification_link_success(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user_by_email = UserAuthSchema(
        id=1,
        email="andrew@mail.com",
        email_verified=False,
        first_name="Temp",
        date_of_birth=date(2000, 2, 21),
        password="hashed_password",
        is_deceased=False,
        is_active=True,
    )
    user_service.get_user_by_email.return_value = user_by_email
    monkeypatch.setattr(
        "modules.auth.services.auth_service.UserPolicy.can_verify_email",
        Mock(return_value=user_by_email),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.TokenService.create_verification_token",
        Mock(return_value="token"),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.create_link_with_token",
        Mock(return_value="http://localhost/verify?token=token"),
    )
    send_mock = Mock()
    monkeypatch.setattr(
        "modules.auth.services.auth_service.send_verification_link_email_task",
        send_mock,
    )

    # Act
    await auth_service.resend_verification_link(
        UserVerifySchema(
            email="andrew@mail.com",
        )
    )

    # Assert
    send_mock.send.assert_called_once_with(
        to_email=user_by_email.email,
        link="http://localhost/verify?token=token",
    )


@pytest.mark.asyncio
async def test_resend_verification_link_email_already_verified(
    auth_service: AuthService,
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    user_by_email = UserAuthSchema(
        id=1,
        email="andrew@mail.com",
        email_verified=True,
        first_name="Temp",
        date_of_birth=date(2000, 2, 21),
        password="hashed_password",
        is_deceased=False,
        is_active=True,
    )
    user_service.get_user_by_email.return_value = user_by_email
    monkeypatch.setattr(
        "modules.auth.services.auth_service.UserPolicy.can_verify_email",
        Mock(return_value=user_by_email),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.TokenService.create_verification_token",
        Mock(return_value="token"),
    )
    monkeypatch.setattr(
        "modules.auth.services.auth_service.create_link_with_token",
        Mock(return_value="http://localhost/verify?token=token"),
    )
    send_mock = Mock()
    monkeypatch.setattr(
        "modules.auth.services.auth_service.send_verification_link_email_task",
        send_mock,
    )

    # Act
    await auth_service.resend_verification_link(
        UserVerifySchema(
            email="andrew@mail.com",
        )
    )

    # Assert
    send_mock.send.assert_not_called()
