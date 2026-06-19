from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.engine import get_async_session
from infrastructure.filter import Filter
from modules.capsules.filter import CapsuleFilter
from modules.capsules.repository import CapsuleRepository
from modules.capsules.schemas import CapsuleFilterSchema
from modules.capsules.service import CapsuleService


async def get_capsule_repository(
    session: AsyncSession = Depends(get_async_session),
):
    return CapsuleRepository(session=session)


async def get_capsule_service(
    repository: CapsuleRepository = Depends(get_capsule_repository),
):
    return CapsuleService(repository=repository)


def get_capsule_filter(
    capsule_filter: CapsuleFilterSchema = Depends(),
) -> Filter:
    data = capsule_filter.model_dump()
    return CapsuleFilter(**data)
