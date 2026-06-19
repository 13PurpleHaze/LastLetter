from typing import TypeVar, Generic

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponseSchema(BaseModel, Generic[T]):
    success: bool = True
    result: T | None = None
    message: str | None = None
