from typing import Callable

from sqlalchemy import Select

from infrastructure.db.models import Capsule
from infrastructure.filter import Filter
from datetime import datetime


class CapsuleFilter(Filter):
    def get_callbacks(self) -> dict[str, Callable]:
        return {
            "search": CapsuleFilter.search,
            "created_from": CapsuleFilter.created_from,
            "created_to": CapsuleFilter.created_to,
        }

    @staticmethod
    def search(stmt: Select, value: str) -> Select:
        return stmt.where(Capsule.title.like(f"%{value}%"))

    @staticmethod
    def created_from(stmt: Select, value: datetime) -> Select:
        return stmt.where(Capsule.created_at >= value)

    @staticmethod
    def created_to(stmt: Select, value: datetime) -> Select:
        return stmt.where(Capsule.created_at <= value)
