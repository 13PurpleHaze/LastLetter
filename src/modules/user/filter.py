from typing import Callable

from sqlalchemy import Select

from core.constants import RoleSlug
from infrastructure.db.models import User, UserRole, Role
from infrastructure.filter import Filter


class UserFilter(Filter):
    def get_callbacks(self) -> dict[str, Callable]:
        return {
            "email": UserFilter.email,
            "role_slug": UserFilter.role_slug,
        }

    @staticmethod
    def email(stmt: Select, value: str) -> Select:
        return stmt.where(User.email.ilike(f"%{value}%"))

    @staticmethod
    def role_slug(stmt: Select, value: RoleSlug) -> Select:
        return (
            stmt.join(UserRole, User.id == UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.slug == value)
        )
