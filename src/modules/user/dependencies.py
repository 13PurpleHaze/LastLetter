from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.engine import get_async_session
from .filter import UserFilter
from .repository import UserRepository
from .service import UserService
from .schemas import UserFilterSchema


async def get_user_repository(
    session: AsyncSession = Depends(get_async_session),
) -> UserRepository:
    return UserRepository(session=session)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository)


def get_user_filter(
    user_filter: UserFilterSchema = Depends(),
):
    data = user_filter.model_dump()
    return UserFilter(**data)
