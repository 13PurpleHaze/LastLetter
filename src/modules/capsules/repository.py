from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy.sql import select, delete, func
from datetime import datetime

from core.constants import RoleSlug
from infrastructure.db.models import UserCapsule, Content, ParentChild, Role
from modules.capsules.factories import (
    CapsuleSchemaFactory,
    ContentSchemaFactory,
    CapsuleLightSchemaFactory,
    UserCapsuleSchemaFactory,
)
from modules.capsules.schemas import (
    CapsuleCreateSchema,
    CapsuleSchema,
    ContentSchema,
    ContentCreateSchema,
    UserCapsuleSchema,
    CapsuleUpdateSchema,
    CapsuleLightSchema,
)
from infrastructure.db.models.capsule import Capsule
from infrastructure.filter import Filter
from infrastructure.db.models import User


class CapsuleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_capsules_by_recipient(
        self, recipient_id: int, filter: Filter, limit: int, offset: int
    ) -> tuple[list[CapsuleLightSchema], int]:
        creator = aliased(User)
        stmt = (
            select(Capsule)
            .join(User.capsules)
            .where(User.id == recipient_id)
            .join(creator, creator.id == Capsule.creator_id)
            .where(creator.is_deceased, datetime.now() > Capsule.send_at)
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
            CapsuleLightSchemaFactory.model_to_schema(capsule=capsule)
            for capsule in capsules
        ], total

    async def get_capsule_by_recipient_by_id(
        self, capsule_id: int, recipient_id
    ) -> CapsuleSchema | None:
        creator = aliased(User)
        stmt = (
            select(Capsule)
            .where(Capsule.id == capsule_id)
            .join(User.capsules)
            .where(User.id == recipient_id)
            .join(creator, creator.id == Capsule.creator_id)
            .where(creator.is_deceased, datetime.now() > Capsule.send_at)
        )
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        return CapsuleSchemaFactory.model_to_schema(capsule) if capsule else None

    async def get_capsules_by_creator(
        self,
        creator_id: int,
        filter: Filter,
        limit: int,
        offset: int,
    ) -> tuple[list[CapsuleLightSchema], int]:
        stmt = select(Capsule).where(Capsule.creator_id == creator_id)
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
            CapsuleLightSchemaFactory.model_to_schema(capsule=capsule)
            for capsule in capsules
        ], total

    async def get_capsule_with_relations_by_id(
        self, capsule_id: int
    ) -> CapsuleSchema | None:
        stmt = (
            select(Capsule)
            .where(Capsule.id == capsule_id)
            .options(
                selectinload(Capsule.users),
                selectinload(Capsule.contents),
                selectinload(Capsule.creator),
            )
        )
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        return CapsuleSchemaFactory.model_to_schema(capsule) if capsule else None

    async def get_capsule_by_id(self, capsule_id: int) -> CapsuleLightSchema | None:
        stmt = select(Capsule).where(Capsule.id == capsule_id)
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        return CapsuleLightSchemaFactory.model_to_schema(capsule) if capsule else None

    async def get_capsules_by_creator_with_relations(
        self, creator_id: int
    ) -> list[CapsuleSchema]:
        stmt = (
            select(Capsule)
            .where(Capsule.creator_id == creator_id)
            .options(
                selectinload(Capsule.users),
                selectinload(Capsule.contents),
                selectinload(Capsule.creator),
            )
        )
        result = await self.session.execute(stmt)
        capsules = result.scalars().all()
        return (
            [
                CapsuleSchemaFactory.model_to_schema(capsule=capsule)
                for capsule in capsules
            ]
            if capsules
            else []
        )

    async def create_capsule(
        self, capsule_create: CapsuleCreateSchema, creator_id: int
    ) -> CapsuleLightSchema:
        capsule = Capsule(
            title=capsule_create.title,
            text=capsule_create.text,
            creator_id=creator_id,
        )
        self.session.add(capsule)
        await self.session.commit()
        await self.session.refresh(capsule)
        return CapsuleLightSchemaFactory.model_to_schema(capsule=capsule)

    async def update_capsule(
        self, capsule_id: int, capsule_update: CapsuleUpdateSchema
    ) -> CapsuleSchema | None:
        stmt = (
            select(Capsule)
            .where(Capsule.id == capsule_id)
            .options(
                selectinload(Capsule.users),
                selectinload(Capsule.contents),
                selectinload(Capsule.creator),
            )
        )
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        if not capsule:
            return None
        if capsule_update.text is not None:
            capsule.text = capsule_update.text
        if capsule_update.title is not None:
            capsule.title = capsule_update.title
        if capsule_update.send_at is not None:
            capsule.send_at = capsule_update.send_at.replace(tzinfo=None)
        await self.session.commit()
        await self.session.refresh(capsule)
        return CapsuleSchemaFactory.model_to_schema(capsule=capsule)

    async def delete_capsule(self, capsule_id: int):
        stmt = delete(Capsule).where(Capsule.id == capsule_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_content_by_id(self, content_id: int) -> ContentSchema | None:
        stmt = select(Content).where(Content.id == content_id)
        result = await self.session.execute(stmt)
        capsule = result.scalar_one_or_none()
        return ContentSchemaFactory.model_to_schema(capsule) if capsule else None

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

    async def delete_content(self, capsule_id: int, content_id: int):
        stmt = delete(Content).where(
            Content.id == content_id,
            Content.capsule_id == capsule_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def can_attach_user(
        self,
        *,
        capsule_id: int,
        current_user_id: int,
        target_user_id: int,
    ) -> bool:
        stmt = (
            select(User.id)
            .join(User.roles)
            .join(ParentChild, ParentChild.child_id == User.id)
            .join(Capsule, Capsule.id == capsule_id)
            .where(
                Capsule.id == capsule_id,
                Capsule.creator_id == current_user_id,
                User.id == target_user_id,
                Role.slug == RoleSlug.CHILD,
                ParentChild.parent_id == current_user_id,
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar() is not None

    async def attach_user(
        self, capsule_id: int, user_id: int, send_at: datetime | None = None
    ) -> UserCapsuleSchema:
        user_capsule = UserCapsule(
            capsule_id=capsule_id,
            user_id=user_id,
        )
        self.session.add(user_capsule)
        await self.session.commit()
        return UserCapsuleSchemaFactory.model_to_schema(user_capsule=user_capsule)

    async def detach_user(self, capsule_id: int, user_id: int):
        stmt = delete(UserCapsule).where(
            UserCapsule.capsule_id == capsule_id, UserCapsule.user_id == user_id
        )
        await self.session.execute(stmt)
        await self.session.commit()
