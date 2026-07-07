from modules.capsules.exceptions import (
    CapsuleNotFoundError,
    CapsuleNotAccessibleError,
    ContentNotFoundError,
)
from modules.capsules.schemas import CapsuleLightSchema, CapsuleSchema, ContentSchema
from modules.user.schemas import UserInternalSchema, CurrentUserSchema
from datetime import datetime


class CapsulePolicy:
    @staticmethod
    def _user_creator(user_id: int, creator_id: int) -> bool:
        return creator_id == user_id

    @staticmethod
    def _user_recipient(user_id: int, capsule: CapsuleSchema) -> bool:
        return any(u.id == user_id for u in capsule.users)

    @staticmethod
    def can_view(
        user: CurrentUserSchema, capsule: CapsuleSchema | None, capsule_id: int
    ):
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        is_creator = CapsulePolicy._user_creator(
            user_id=user.id, creator_id=capsule.creator.id
        )
        is_recipient = CapsulePolicy._user_recipient(user_id=user.id, capsule=capsule)
        if not (is_creator or is_recipient):
            raise CapsuleNotAccessibleError(capsule_id=capsule_id, user_id=user.id)
        if is_recipient:
            if not capsule.creator.is_deceased:
                raise CapsuleNotFoundError(capsule_id)
            if capsule.send_at and datetime.now() < capsule.send_at:
                raise CapsuleNotFoundError(capsule_id)

    @staticmethod
    def can_interact(
        capsule: CapsuleLightSchema | None, capsule_id: int, user: UserInternalSchema
    ) -> CapsuleLightSchema:
        if not capsule:
            raise CapsuleNotFoundError(capsule_id=capsule_id)
        is_creator = CapsulePolicy._user_creator(capsule.creator_id, user.id)
        if not is_creator:
            raise CapsuleNotAccessibleError(capsule_id=capsule_id, user_id=user.id)
        return capsule


class ContentPolicy:
    @staticmethod
    def _content_exists(
        content: ContentSchema | None, content_id: int
    ) -> ContentSchema:
        if not content:
            raise ContentNotFoundError(content_id=content_id)
        return content

    @staticmethod
    def _capsule_content(content: ContentSchema, capsule_id: int, user_id: int):
        if content.capsule_id != capsule_id:
            raise CapsuleNotAccessibleError(user_id=user_id, capsule_id=capsule_id)

    @staticmethod
    def can_interact(
        content: ContentSchema | None, capsule_id: int, user_id: int, content_id: int
    ) -> ContentSchema:
        content = ContentPolicy._content_exists(content=content, content_id=content_id)
        ContentPolicy._capsule_content(
            content=content, capsule_id=capsule_id, user_id=user_id
        )
        return content
