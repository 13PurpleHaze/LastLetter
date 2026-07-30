import pytest
from unittest.mock import Mock, AsyncMock

from modules.auth.services.auth_service import AuthService


@pytest.fixture
def user_service():
    service = Mock()

    service.get_user_by_email = AsyncMock()
    service.create_user = AsyncMock()
    service.get_user_with_roles_by_id = AsyncMock()
    service.update_user = AsyncMock()

    return service


@pytest.fixture
def auth_service(user_service):
    return AuthService(user_service=user_service)
