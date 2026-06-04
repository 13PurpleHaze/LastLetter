from typing import TypeVar, Generic, Optional

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponseSchema(BaseModel, Generic[T]):
    success: bool = True
    result: Optional[T] = None
