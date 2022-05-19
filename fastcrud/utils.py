from fastapi import Query
from pydantic import BaseModel, Field


def pagination_factory(max_limit: int):
    class PaginationPydantic(BaseModel):
        offset: int = Field(default=0)
        limit: int = Field(default=max_limit)

    def get_pagination_filter(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=max_limit, le=max_limit)
    ) -> PaginationPydantic:
        return PaginationPydantic(offset=offset, limit=limit)

    return get_pagination_filter
