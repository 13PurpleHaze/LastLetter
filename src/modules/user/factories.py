from infrastructure.db.models import User, Role
from .schemas import (
    UserSchema,
    RoleSchema,
    CurrentUserSchema,
    UserLightSchema,
    UserAuthSchema,
)


class UserSchemaFactory:
    @classmethod
    def model_to_schema(cls, user: User) -> UserSchema:
        return UserSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            date_of_birth=user.date_of_birth,
            is_deceased=user.is_deceased,
            email_verified=user.email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            verificator=(
                UserLightSchemaFactory.model_to_schema(user=user.verificator)
                if user.verificator
                else None
            ),
            family=[
                UserLightSchemaFactory.model_to_schema(fm)
                for fm in user.parents + user.children
            ],
            roles=[RoleSchemaFactory.model_to_schema(role) for role in user.roles],
        )


class UserLightSchemaFactory:
    @staticmethod
    def model_to_schema(user: User) -> UserLightSchema:
        return UserLightSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            is_deceased=user.is_deceased,
        )


class CurrentUserSchemaFactory:
    @staticmethod
    def model_to_schema(user: User) -> CurrentUserSchema:
        return CurrentUserSchema(
            id=user.id,
            is_active=user.is_active,
            email_verified=user.email_verified,
            first_name=user.first_name,
            email=user.email,
            verificator_id=user.verificator_id,
            roles=[RoleSchemaFactory.model_to_schema(role) for role in user.roles],
        )


class RoleSchemaFactory:
    @staticmethod
    def model_to_schema(role: Role) -> RoleSchema:
        return RoleSchema(
            id=role.id,
            slug=role.slug,
            title=role.title,
        )


class UserAuthSchemaFactory:
    @staticmethod
    def model_to_schema(user: User) -> UserAuthSchema:
        return UserAuthSchema(
            id=user.id,
            password=user.password,
            email_verified=user.email_verified,
            is_active=user.is_active,
            email=user.email,
        )
