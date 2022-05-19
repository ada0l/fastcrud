from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


class PaginationPydantic(BaseModel):
    offset: int = Field(default=0)
    limit: int = Field(default=100)


DataT = TypeVar('DataT')


class ListPydantic(GenericModel, Generic[DataT]):
    items: list[DataT]
    count: int
