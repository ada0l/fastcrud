from typing import Callable, Generic, TypeVar, Type

from fastapi import APIRouter, Depends
from fastapi.types import DecoratedCallable
from pydantic import BaseModel

from .exceptions import NotFoundException
from .schemas import ListPydantic
from .utils import pagination_factory

T = TypeVar("T", bound=BaseModel)


class RouterGenerator(Generic[T], APIRouter):

    def __init__(
        self,
        response_model: Type[T],
        tags: list[str] | None = None,
        pagination: int | None = 100,
        prefix: str = "",
        get_all: bool = True,
        get_one: bool = True,
        get_repository_function: any = None,
        **kwargs: any
    ):
        self.pagination = pagination
        self.response_model = response_model
        self.get_repository_function = get_repository_function
        tags = tags or [prefix.strip("/")]
        super().__init__(prefix=prefix, tags=tags, **kwargs)

        if get_all:
            super().add_api_route(
                "/",
                self._get_all(),
                response_model=ListPydantic[self.response_model]
            )

        if get_one:
            super().add_api_route(
                "/{item_id}",
                self._get_one(),
                response_model=self.response_model
            )

    def remove_api_route(self, path: str, methods: list[str]) -> None:
        methods_ = set(methods)

        for route in self.routes:
            if (
                route.path == f"{self.prefix}{path}"
                and route.methods == methods_
            ):
                self.routes.remove(route)

    def get(
        self, path: str, *args: any, **kwargs: any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["GET"])
        return super().get(path, *args, **kwargs)

    def _get_one(self) -> Callable[..., any]:

        async def get_one_endpoint(
            item_id: int,
            rep=Depends(self.get_repository_function)
        ):
            obj = await rep.get_by_id(item_id)
            if not obj:
                raise NotFoundException
            return obj

        return get_one_endpoint

    def _get_all(self) -> Callable[..., any]:

        async def get_all_endpoint(
            pagination=Depends(pagination_factory(self.pagination)),
            rep=Depends(self.get_repository_function)
        ):
            items = await rep.get_multi(pagination)
            return {
                "items": items,
                "count": len(items)
            }

        async def get_all_endpoint_without_pagination(
            rep=Depends(self.get_repository_function)
        ):
            items = await rep.get_multi()
            return {
                "items": items,
                "count": len(items)
            }

        if self.pagination is None:
            return get_all_endpoint_without_pagination

        return get_all_endpoint
