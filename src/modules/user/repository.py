from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, insert

from infrastructure.db.models import User, Role, UserRole
from modules.user.schemas import UserSchema, UserCreateSchema
from .factories import UserSchemaFactory


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> UserSchema | None:
        stmt = select(User).where(User.email == email).options(selectinload(User.roles))
        result = await self.session.execute(stmt)
        user = result.unique().scalar_one_or_none()
        if user:
            return UserSchemaFactory.model_to_schema(user=user)
        else:
            return None

    async def get_user_by_id(self, user_id: int) -> UserSchema | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.session.execute(stmt)
        user = result.unique().scalar_one_or_none()
        if user:
            return UserSchemaFactory.model_to_schema(user=user)
        else:
            return None

    async def create_user(
        self, user_create: UserCreateSchema, role_ids: list[int]
    ) -> UserSchema:
        user = User(
            first_name=user_create.first_name,
            email=user_create.email,
            password=user_create.password,
            date_of_birth=user_create.date_of_birth,
        )

        self.session.add(user)
        result = await self.session.execute(select(Role).where(Role.id.in_(role_ids)))
        roles = result.scalars().all()
        user.roles.extend(roles)

        await self.session.commit()

        return UserSchemaFactory.model_to_schema(user=user)

    async def add_roles_to_user(self, user_id: int, role_ids: list[int]) -> None:
        if not role_ids:
            return
        stmt = insert(UserRole).values(
            [{"user_id": user_id, "role_id": rid} for rid in role_ids]
        )
        await self.session.execute(stmt)

    async def verify_email(self, user_id: int):
        user = await self.session.get(User, user_id)
        if user:
            user.email_verified = True
            await self.session.commit()
