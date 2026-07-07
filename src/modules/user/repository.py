from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, insert, func

from infrastructure.db.models import User, Role, UserRole, ParentChild
from infrastructure.filter import Filter
from modules.user.schemas import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserLightSchema,
    UserAuthSchema,
)
from .factories import (
    UserSchemaFactory,
    CurrentUserSchemaFactory,
    UserLightSchemaFactory,
    UserAuthSchemaFactory,
)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users(
        self,
        filter: Filter,
        limit: int,
        offset: int,
    ) -> tuple[list[UserLightSchema], int]:
        stmt = filter.apply(select(User))
        total = await self.session.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        total = total or 0
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        users = result.scalars().all()

        if not users:
            return [], total
        return [
            UserLightSchemaFactory.model_to_schema(user=user) for user in users
        ], total

    async def get_users_for_verify(
        self, current_user_id: int, limit: int, offset: int
    ) -> tuple[list[UserLightSchema], int]:
        stmt = select(User).where(User.verificator_id == current_user_id)

        total = await self.session.scalar(
            select(func.count()).where(User.verificator_id == current_user_id)
        )
        total = total or 0

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        users = result.scalars().all()

        return [
            UserLightSchemaFactory.model_to_schema(user=user) for user in users
        ], total

    async def get_user_with_roles_by_id(self, user_id: int):
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return CurrentUserSchemaFactory.model_to_schema(user=user) if user else None

    async def get_user_by_email(self, email: str) -> UserAuthSchema | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return UserAuthSchemaFactory.model_to_schema(user=user) if user else None

    async def get_user_by_id(self, user_id: int) -> UserSchema | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles),
                selectinload(User.parents),
                selectinload(User.children),
                selectinload(User.verificator),
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return UserSchemaFactory.model_to_schema(user=user) if user else None

    async def create_user(
        self, user_create: UserCreateSchema, roles: list[str]
    ) -> UserLightSchema:
        user = User(
            first_name=user_create.first_name,
            email=user_create.email,
            password=user_create.password,
            date_of_birth=user_create.date_of_birth,
        )

        self.session.add(user)
        result = await self.session.execute(select(Role).where(Role.slug.in_(roles)))
        role_models = result.scalars().all()
        user.roles.extend(role_models)

        await self.session.commit()

        return UserLightSchemaFactory.model_to_schema(user=user)

    async def add_roles_to_user(self, user_id: int, roles: list[str]):
        result = await self.session.execute(select(Role).where(Role.slug.in_(roles)))
        role_models = result.scalars().all()
        stmt = insert(UserRole).values(
            [{"user_id": user_id, "role_id": role.id} for role in role_models]
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def invite_user(self, user_id: int, inviter_id: int) -> None:
        stmt = insert(ParentChild).values(
            [{"parent_id": inviter_id, "child_id": user_id}]
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_user(
        self, user_id: int, user_update: UserUpdateSchema
    ) -> UserSchema | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles),
                selectinload(User.parents),
                selectinload(User.children),
                selectinload(User.verificator),
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            update_data = user_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            await self.session.commit()
            await self.session.refresh(user)
            return UserSchemaFactory.model_to_schema(user=user)
        return None
