from utils.auth.secure import hash_password
from .repository import UserRepository
from .schemas import UserSchema, UserCreateSchema


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(
        self, user_create: UserCreateSchema, role_ids: list[int]
    ) -> UserSchema:
        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password
        return await self.repository.create_user(
            user_create=user_create, role_ids=role_ids
        )

    async def get_user_by_email(self, email: str) -> UserSchema | None:
        return await self.repository.get_user_by_email(email)

    async def get_user_by_id(self, user_id: int) -> UserSchema | None:
        return await self.repository.get_user_by_id(user_id)

    async def verify_email(self, user_id: int):
        await self.repository.verify_email(user_id=user_id)
