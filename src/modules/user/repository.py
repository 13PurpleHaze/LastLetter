from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, insert, func

from infrastructure.db.models import User, Role, UserRole, ParentChild
from infrastructure.filter import Filter
from modules.user.schemas import UserSchema, UserCreateSchema, UserUpdateSchema
from .factories import UserSchemaFactory, CurrentUserSchemaFactory
from datetime import datetime
from modules.user.schemas import CurrentUserSchema


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users(
        self,
        limit: int,
        offset: int,
        filter: Filter,
    ) -> tuple[list[CurrentUserSchema], int]:
        stmt = select(User).options(
            selectinload(User.roles),
            selectinload(User.parents).selectinload(User.roles),
            selectinload(User.children).selectinload(User.roles),
        )
        stmt = filter.apply(stmt)
        total = await self.session.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        total = total or 0
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        users = result.scalars().all()

        if not users:
            return [], 0
        return [
            CurrentUserSchemaFactory.model_to_schema(user=user) for user in users
        ], total

    async def get_users_for_verify(
        self, current_user: CurrentUserSchema, limit: int, offset: int
    ) -> tuple[list[CurrentUserSchema], int]:
        stmt = (
            select(User)
            .where(User.verificator_id == current_user.id)
            .options(
                selectinload(User.roles),
                selectinload(User.parents).selectinload(User.roles),
                selectinload(User.children).selectinload(User.roles),
            )
        )

        total = await self.session.scalar(
            select(func.count()).where(User.verificator_id == current_user.id)
        )
        total = total or 0

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        users = result.scalars().all()

        return [
            CurrentUserSchemaFactory.model_to_schema(user=user) for user in users
        ], total

    async def get_user_by_email(self, email: str) -> UserSchema | None:
        stmt = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.roles),
                selectinload(User.parents).selectinload(User.roles),
                selectinload(User.children).selectinload(User.roles),
            )
        )
        try:
            result = await self.session.execute(stmt)
        except Exception as e:
            print(e)
            raise e
        user = result.unique().scalar_one_or_none()
        if user:
            return UserSchemaFactory.model_to_schema(user=user)
        else:
            return None

    async def get_user_by_id(self, user_id: int) -> UserSchema | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles),
                selectinload(User.parents).selectinload(User.roles),
                selectinload(User.children).selectinload(User.roles),
            )
        )

        result = await self.session.execute(stmt)

        user = result.unique().scalar_one_or_none()

        if user:
            return UserSchemaFactory.model_to_schema(user=user)
        else:
            return None

    async def create_user(
        self, user_create: UserCreateSchema, roles: list[str]
    ) -> UserSchema:
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

        return UserSchemaFactory.model_to_schema(user=user)

    async def add_roles_to_user(self, user_id: int, roles: list[str]) -> None:
        if not roles:
            return
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
        print(stmt)
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
                selectinload(User.parents).selectinload(User.roles),
                selectinload(User.children).selectinload(User.roles),
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            if user_update.email is not None:
                user.email = str(user_update.email)
                user.email_verified = False
            if user_update.first_name is not None:
                user.first_name = user_update.first_name
            if user_update.date_of_birth:
                user.date_of_birth = datetime.combine(
                    user_update.date_of_birth, datetime.now().time()
                )
            if user_update.password is not None:
                user.password = user_update.password
            if user_update.email_verified is not None:
                user.email_verified = user_update.email_verified
            if user_update.is_deceased is not None:
                user.is_deceased = user_update.is_deceased
            if user_update.verificator_id is not None:
                user.verificator_id = user_update.verificator_id

            await self.session.commit()
            await self.session.refresh(user)
            return UserSchemaFactory.model_to_schema(user=user)
        return None
