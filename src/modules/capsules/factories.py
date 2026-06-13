from infrastructure.db.models import Capsule, Content, UserCapsule
from .schemas import CapsuleSchema, ContentSchema, CapsuleUserSchema
from ..user.factories import CurrentUserSchemaFactory


class ContentSchemaFactory:
    @staticmethod
    def model_to_schema(content: Content) -> ContentSchema:
        return ContentSchema(
            id=content.id,
            object_key=content.object_key,
            size_bytes=content.size_bytes,
            order_index=content.order_index,
            content_type=content.content_type,
        )


class CapsuleSchemaFactory:
    @staticmethod
    def model_to_schema(capsule: Capsule) -> CapsuleSchema:
        return CapsuleSchema(
            id=capsule.id,
            title=capsule.title,
            text=capsule.text,
            creator_id=capsule.creator_id,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
            users=[
                CurrentUserSchemaFactory.model_to_schema(user) for user in capsule.users
            ],
            contents=[
                ContentSchemaFactory.model_to_schema(content=content)
                for content in capsule.contents
            ],
        )


class CapsuleUserFactory:
    @staticmethod
    def model_to_schema(user_capsule: UserCapsule) -> CapsuleUserSchema:
        return CapsuleUserSchema(
            capsule_id=user_capsule.capsule_id,
            user_id=user_capsule.user_id,
            send_at=user_capsule.send_at,
            sent_at=user_capsule.sent_at,
            is_sent=user_capsule.is_sent,
        )
