import pytest
from datetime import date

from unittest.mock import Mock

from core.constants import RoleSlug
from modules.auth.schemas import UserRegisterSchema
from modules.user.exceptions import UserAlreadyExistsError


## Register
@pytest.mark.asyncio
async def test_register_success(auth_service, user_service, mocker):
    register_schema = UserRegisterSchema(
        email="test@test.com",
        password="password123",
        first_name="test_first_name",
        date_of_birth=date.today(),
        is_parent=True,
        is_child=False,
        is_verifier=False,
    )

    user_create = Mock(
        email="test@test.com",
        password="123",
    )

    created_user = Mock(
        id=1,
        email="test@test.com",
    )

    user_service.get_user_by_email.return_value = None
    user_service.create_user.return_value = created_user

    mocker.patch(
        "modules.auth.services.auth_service.AuthSchemaFactory.user_register_schema_to_user_create_schema",
        return_value=user_create,
    )
    mocker.patch(
        "modules.auth.services.auth_service.hash_password",
        return_value="hashed_password",
    )

    mocker.patch(
        "modules.auth.services.auth_service.TokenService.create_verification_token",
        return_value="verification_token",
    )

    mocker.patch(
        "modules.auth.services.auth_service.create_link_with_token",
        return_value="http://test.com/verify",
    )
    send_email_mock = mocker.patch(
        "modules.auth.services.auth_service.send_verification_link_email_task.send"
    )

    result = await auth_service.register(register_schema)

    assert result == created_user
    user_service.get_user_by_email.assert_awaited_once_with(email="test@test.com")
    user_service.create_user.assert_awaited_once()
    assert user_create.password == "hashed_password"

    send_email_mock.assert_called_once_with(
        to_email="test@test.com",
        link="http://test.com/verify",
    )

    user_service.create_user.assert_awaited_once_with(
        user_create=user_create,
        roles=[RoleSlug.PARENT.value],
    )


@pytest.mark.asyncio
async def test_register_user_already_exists(auth_service, user_service):
    register_schema = Mock(
        email="test@test.com",
    )

    existing_user = Mock(
        email="test@test.com",
    )

    user_service.get_user_by_email.return_value = existing_user

    with pytest.raises(UserAlreadyExistsError) as exc:
        await auth_service.register(register_schema)

    user_service.get_user_by_email.assert_awaited_once_with(email="test@test.com")
    user_service.create_user.assert_not_awaited()

    assert exc.value.email == "test@test.com"


@pytest.mark.asyncio
async def test_register_assigns_parent_role(user_service, auth_service, mocker):
    register_schema = UserRegisterSchema(
        email="parent@test.com",
        password="password123",
        first_name="parent",
        date_of_birth=date.today(),
        is_parent=True,
        is_child=False,
        is_verifier=False,
    )

    user_create = Mock(
        email="parent@test.com",
        password="plain_password",
    )

    created_user = Mock(
        id=1,
        email="parent@test.com",
    )

    user_service.get_user_by_email.return_value = None
    user_service.create_user.return_value = created_user

    mocker.patch(
        "modules.auth.services.auth_service.AuthSchemaFactory.user_register_schema_to_user_create_schema",
        return_value=user_create,
    )

    mocker.patch(
        "modules.auth.services.auth_service.hash_password",
        return_value="hashed_password",
    )

    mocker.patch(
        "modules.auth.services.auth_service.TokenService.create_verification_token",
        return_value="verification_token",
    )

    mocker.patch(
        "modules.auth.services.auth_service.create_link_with_token",
        return_value="http://test.com/verify",
    )

    mocker.patch(
        "modules.auth.services.auth_service.send_verification_link_email_task.send"
    )

    await auth_service.register(register_schema)

    user_service.create_user.assert_awaited_once_with(
        user_create=user_create,
        roles=[RoleSlug.PARENT.value],
    )
