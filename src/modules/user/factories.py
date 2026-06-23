from infrastructure.db.models import User, Role
from .schemas import UserSchema, RoleSchema, CurrentUserSchema, FamilyMemberSchema


class UserSchemaFactory:
    @classmethod
    def model_to_schema(cls, user: User) -> UserSchema:
        print(user)
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
            verificator_id=user.verificator_id,
            family=[
                FamilyMemberSchemaFactory.model_to_schema(fm)
                for fm in user.parents + user.children
            ],
            roles=[RoleSchemaFactory.model_to_schema(role) for role in user.roles],
        )


class CurrentUserSchemaFactory:
    @staticmethod
    def user_schema_to_current_user_schema(user: UserSchema) -> CurrentUserSchema:
        return CurrentUserSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            date_of_birth=user.date_of_birth,
            roles=user.roles,
            is_active=user.is_active,
            email_verified=user.email_verified,
            family=user.family,
            is_deceased=user.is_deceased,
            verificator_id=user.verificator_id,
        )

    @staticmethod
    def model_to_schema(user: User) -> CurrentUserSchema:
        return CurrentUserSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            date_of_birth=user.date_of_birth,
            is_active=user.is_active,
            email_verified=user.email_verified,
            family=[
                FamilyMemberSchemaFactory.model_to_schema(fm)
                for fm in user.parents + user.children
            ],
            is_deceased=user.is_deceased,
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


class FamilyMemberSchemaFactory:
    @staticmethod
    def model_to_schema(user: User) -> FamilyMemberSchema:
        return FamilyMemberSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            roles=[RoleSchemaFactory.model_to_schema(role) for role in user.roles],
        )
