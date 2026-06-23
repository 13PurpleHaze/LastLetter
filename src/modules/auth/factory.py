from modules.auth.schemas import UserRegisterSchema
from modules.user.schemas import UserCreateSchema


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
