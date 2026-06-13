from pydantic import BaseModel, Field
from typing import TypeVar, Generic

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(10, gt=0, le=100)
    offset: int = Field(0, ge=0)


class PageMetaSchema(BaseModel):
    limit: int
    offset: int
    total: int


class ListResponseSchema(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMetaSchema
