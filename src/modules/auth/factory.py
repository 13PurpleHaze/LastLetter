from modules.auth.schemas import UserRegisterSchema
from modules.user.schemas import UserCreateSchema, UserSchema, CurrentUserSchema


class AuthSchemaFactory:
    @classmethod
    def user_register_schema_to_user_create_schema(
        cls, user: UserRegisterSchema
    ) -> UserCreateSchema:
        return UserCreateSchema(
            first_name=user.first_name,
            password=user.password,
            email=user.email,
            date_of_birth=user.date_of_birth,
        )

    @classmethod
    def user_schema_to_current_user_schema(cls, user: UserSchema) -> CurrentUserSchema:
        return CurrentUserSchema(
            id=user.id,
            first_name=user.first_name,
            email=user.email,
            roles=user.roles,
            date_of_birth=user.date_of_birth,
            is_active=user.is_active,
            email_verified=user.email_verified,
        )
