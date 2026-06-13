from abc import ABC, abstractmethod
from typing import Callable

from sqlalchemy import Select


class Filter(ABC):
    def __init__(self, **kwargs):
        self._filters = {}
        for key, value in kwargs.items():
            if value is not None:
                self._filters[key] = value

    @abstractmethod
    def get_callbacks(self) -> dict[str, Callable]:
        pass

    def apply(self, stmt: Select):
        for field, callback in self.get_callbacks().items():
            if field in self._filters:
                stmt = callback(stmt, self._filters[field])
        return stmt
