from typing import Type

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker

from examples.database import database_url
from fastcrud.base_repository import BaseRepository
from fastcrud.router_generator import RouterGenerator

engine = create_async_engine(database_url, future=True, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@as_declarative()
class Base:
    __name__: str

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class SomeItem(Base):
    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)


class SomeItemBasePydantic(BaseModel):
    label: str


class SomeItemPydantic(SomeItemBasePydantic):
    id: int

    class Config:
        orm_mode = True


class SomeItemRepository(
    BaseRepository[
        SomeItem,
        SomeItemPydantic,
        SomeItemBasePydantic,
        SomeItemBasePydantic
    ]
):

    @property
    def _model(self) -> Type[SomeItem]:
        return SomeItem


async def get_repository(session: AsyncSession = Depends(get_session)):
    return SomeItemRepository(session)


some_item_router = RouterGenerator(
    prefix="/some_item",
    get_repository_function=get_repository,
    response_model=SomeItemPydantic,
    pagination=10
)


@some_item_router.post("/", response_model=SomeItemPydantic)
async def create_some_item(some_item_in: SomeItemBasePydantic, rep: SomeItemRepository = Depends(get_repository)):
    obj = await rep.create(some_item_in)
    return obj


app = FastAPI()
app.include_router(some_item_router)


@app.on_event("startup")
async def startup_event():
    await init_db()
