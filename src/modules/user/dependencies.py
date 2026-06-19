from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.engine import get_async_session
from .repository import UserRepository
from .service import UserService


async def get_user_repository(
    session: AsyncSession = Depends(get_async_session),
) -> UserRepository:
    return UserRepository(session=session)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository)
