from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, delete, func
from datetime import datetime

from infrastructure.db.models import UserCapsule, Content
from modules.capsules.factories import (
    CapsuleSchemaFactory,
    ContentSchemaFactory,
    CapsuleUserFactory,
)
from modules.capsules.schemas import (
    CapsuleCreateSchema,
    CapsuleSchema,
    ContentSchema,
    ContentCreateSchema,
    CapsuleUserSchema,
    CapsuleUpdateSchema,
)
from infrastructure.db.models.capsule import Capsule
from infrastructure.filter import Filter
from modules.user.schemas import CurrentUserSchema
from infrastructure.db.models import User


class CapsuleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_capsules_by_user(
        self,
        current_user: CurrentUserSchema,
        limit: int,
        offset: int,
        filter: Filter,
    ) -> tuple[list[CapsuleSchema], int]:
        stmt = (
            select(Capsule)
            .where(Capsule.creator_id == current_user.id)
            .options(selectinload(Capsule.users).selectinload(User.roles))
            .options(selectinload(Capsule.contents))
        )
        stmt = filter.apply(stmt)
        total = await self.session.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        total = total or 0
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        capsules = result.scalars().all()

        if not capsules:
            return [], 0
        return [
            CapsuleSchemaFactory.model_to_schema(capsule=capsule)
            for capsule in capsules
        ], total

    async def get_capsule_by_id(self, capsule_id: int) -> CapsuleSchema | None:
        stmt = (
            select(Capsule)
            .where(Capsule.id == capsule_id)
            .options(selectinload(Capsule.contents))
            .options(selectinload(Capsule.users).selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        if not capsule:
            return None
        return CapsuleSchemaFactory.model_to_schema(capsule)

    async def get_content_by_id(self, content_id: int) -> ContentSchema | None:
        stmt = select(Content).where(Content.id == content_id)
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        if not capsule:
            return None
        return ContentSchemaFactory.model_to_schema(capsule)

    async def get_capsule_user_by_ids(
        self, capsule_id: int, user_id: int
    ) -> CapsuleUserSchema | None:
        stmt = select(UserCapsule).where(
            UserCapsule.capsule_id == capsule_id, UserCapsule.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_capsule = result.scalar_one_or_none()
        if not user_capsule:
            return None
        return CapsuleUserFactory.model_to_schema(user_capsule=user_capsule)

    async def create_content(
        self, content_create: ContentCreateSchema, capsule_id: int
    ) -> ContentSchema:
        content = Content(
            content_type=content_create.content_type,
            object_key=content_create.object_key,
            order_index=content_create.order_index,
            size_bytes=content_create.size_bytes,
            capsule_id=capsule_id,
        )
        self.session.add(content)
        await self.session.commit()
        return ContentSchemaFactory.model_to_schema(content=content)

    async def create_capsule(
        self, capsule_create: CapsuleCreateSchema, creator_id: int
    ) -> CapsuleSchema:
        capsule = Capsule(
            title=capsule_create.title,
            text=capsule_create.text,
            creator_id=creator_id,
        )
        self.session.add(capsule)
        await self.session.commit()
        await self.session.refresh(
            capsule,
            attribute_names=["users", "contents"],
        )
        return CapsuleSchemaFactory.model_to_schema(capsule=capsule)

    async def delete_capsule(self, capsule_id: int):
        stmt = delete(Capsule).where(Capsule.id == capsule_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def _find_user_capsule(
        self, capsule_id: int, user_id: int
    ) -> UserCapsule | None:
        stmt = select(UserCapsule).where(
            UserCapsule.capsule_id == capsule_id, UserCapsule.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_capsule = result.scalar_one_or_none()
        return user_capsule

    async def attach_user(
        self, capsule_id: int, user_id: int, send_at: datetime | None = None
    ) -> CapsuleUserSchema:
        user_capsule = await self._find_user_capsule(capsule_id, user_id)
        if user_capsule:
            return CapsuleUserFactory.model_to_schema(user_capsule=user_capsule)
        user_capsule = UserCapsule(
            capsule_id=capsule_id,
            user_id=user_id,
            send_at=send_at,
        )
        self.session.add(user_capsule)
        await self.session.commit()
        return CapsuleUserFactory.model_to_schema(user_capsule=user_capsule)

    async def detach_user(self, capsule_id: int, user_id: int):
        stmt = delete(UserCapsule).where(
            UserCapsule.capsule_id == capsule_id, UserCapsule.user_id == user_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_send_date(
        self, capsule_id: int, user_id: int, send_at: datetime
    ) -> CapsuleUserSchema | None:
        stmt = select(UserCapsule).where(
            UserCapsule.user_id == user_id, UserCapsule.capsule_id == capsule_id
        )
        result = await self.session.execute(stmt)
        user_capsule = result.scalar_one_or_none()
        if not user_capsule:
            return None
        user_capsule.send_at = send_at
        await self.session.commit()
        return CapsuleUserFactory.model_to_schema(user_capsule=user_capsule)

    async def update_capsule_text(
        self, capsule_id: int, capsule_update: CapsuleUpdateSchema
    ) -> CapsuleSchema | None:
        stmt = (
            select(Capsule)
            .where(Capsule.id == capsule_id)
            .options(selectinload(Capsule.contents))
            .options(selectinload(Capsule.users))
        )
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        if not capsule:
            return None
        if capsule_update.text is not None:
            capsule.text = capsule_update.text
        if capsule_update.title is not None:
            capsule.title = capsule_update.title
        await self.session.commit()
        return CapsuleSchemaFactory.model_to_schema(capsule=capsule)
