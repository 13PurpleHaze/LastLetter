from api.v1.schemas.pagination import PaginationParams, PageMetaSchema
from infrastructure.filter import Filter
from utils.auth.secure import hash_password
from .repository import UserRepository
from .schemas import UserSchema, UserCreateSchema, UserUpdateSchema, CurrentUserSchema


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_users(
        self,
        filter: Filter,
        pagination: PaginationParams,
    ) -> tuple[list[CurrentUserSchema], PageMetaSchema]:
        users, total = await self.repository.get_users(
            filter=filter,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PageMetaSchema(
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        return users, meta

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

    async def update_user(
        self, user_id: int, user_update: UserUpdateSchema
    ) -> UserSchema | None:
        return await self.repository.update_user(
            user_id=user_id, user_update=user_update
        )
