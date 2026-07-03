from infrastructure.db.models import Capsule, Content, UserCapsule
from .schemas import CapsuleSchema, ContentSchema, UserCapsuleSchema, CapsuleLightSchema
from modules.user.factories import UserLightSchemaFactory


class ContentSchemaFactory:
    @staticmethod
    def model_to_schema(content: Content) -> ContentSchema:
        return ContentSchema(
            id=content.id,
            object_key=content.object_key,
            size_bytes=content.size_bytes,
            order_index=content.order_index,
            content_type=content.content_type,
            capsule_id=content.capsule_id,
        )


class CapsuleLightSchemaFactory:
    @staticmethod
    def model_to_schema(capsule: Capsule) -> CapsuleLightSchema:
        return CapsuleLightSchema(
            id=capsule.id,
            title=capsule.title,
            text=capsule.text,
            send_at=capsule.send_at,
            creator_id=capsule.creator_id,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
        )


class CapsuleSchemaFactory:
    @staticmethod
    def model_to_schema(capsule: Capsule) -> CapsuleSchema:
        return CapsuleSchema(
            id=capsule.id,
            title=capsule.title,
            text=capsule.text,
            creator=UserLightSchemaFactory.model_to_schema(capsule.creator),
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
            send_at=capsule.send_at,
            users=[
                UserLightSchemaFactory.model_to_schema(user) for user in capsule.users
            ],
            contents=[
                ContentSchemaFactory.model_to_schema(content=content)
                for content in capsule.contents
            ],
        )


class UserCapsuleSchemaFactory:
    @staticmethod
    def model_to_schema(user_capsule: UserCapsule) -> UserCapsuleSchema:
        return UserCapsuleSchema(
            capsule_id=user_capsule.capsule_id,
            user_id=user_capsule.user_id,
        )
