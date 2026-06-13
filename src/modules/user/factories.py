from infrastructure.db.models import User, Role
from .schemas import UserSchema, RoleSchema, CurrentUserSchema


class UserSchemaFactory:
    @classmethod
    def model_to_schema(cls, user: User) -> UserSchema:
        return UserSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            password=user.password,
            date_of_birth=user.date_of_birth,
            is_deceased=user.is_deceased,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[RoleSchemaFactory.model_to_schema(role) for role in user.roles],
        )


class RoleSchemaFactory:
    @classmethod
    def model_to_schema(cls, role: Role) -> RoleSchema:
        return RoleSchema(
            id=role.id,
            slug=role.slug,
            title=role.title,
        )


class CurrentUserSchemaFactory:
    @staticmethod
    def model_to_schema(user: User) -> CurrentUserSchema:
        return CurrentUserSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            date_of_birth=user.date_of_birth,
            is_active=user.is_active,
            email_verified=user.email_verified,
            roles=[RoleSchemaFactory.model_to_schema(role) for role in user.roles],
        )
