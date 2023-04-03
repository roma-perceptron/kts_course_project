import typing
from logging import getLogger

from sqlalchemy import delete, select
from sqlalchemy.engine import ChunkedIteratorResult

# if typing.TYPE_CHECKING:
#     from app.web.app import Application
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import ClauseElement

from kts_backend.store.database import db


class BaseAccessor:
    def __init__(self, database):
        self.database = database

    # def __init__(self, app: "Application", *args, **kwargs):
    #     self.app = app
    #     self.logger = getLogger("accessor")
    #     app.on_startup.append(self.connect)
    #     app.on_cleanup.append(self.disconnect)
    #
    # async def connect(self, app: "Application"):
    #     return
    #
    # async def disconnect(self, app: "Application"):
    #     return

    async def execute_query(
        self, query, only_last=False, no_return=False, joined=False
    ):
        async with self.database.session.begin() as session:
            result: ChunkedIteratorResult = await session.execute(query)
            # return result.unique()
            if not no_return:
                if only_last:
                    result = result.fetchone()[0]
                else:
                    result = result.fetchall()
                # if joined:
                #     result = result.unique()#.fetchall()
                return result

    async def execute_query_creation(self, model_with_params):
        async with self.database.session.begin() as session:
            session.add(model_with_params)
            if self.database.app.debug:
                await session.flush()
                await session.rollback()
            else:
                await session.commit()
        return model_with_params

    async def clear_table(self, model: db):
        async with self.database.session.begin() as session:
            await session.execute(delete(model))

    async def get_or_create(self, model: db, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        async with self.database.session.begin() as session:
            query = select(model).filter_by(**kwargs)
            instance = await session.execute(query)
            instance = instance.one_or_none()
            if instance:
                return *instance, False
            else:
                params = {k: v for k, v in kwargs.items() if v}
                instance = model(**params)
                session.add(instance)
                await session.commit()
                return instance, True

    async def update_or_create(self, model: db, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        async with self.database.session.begin() as session:
            query = select(model).filter_by(**kwargs)
            instance = await session.execute(query)
            instance = instance.one_or_none()
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                return instance, False
            else:
                params = {k: v for k, v in kwargs.items() if v}
                instance = model(**params)
                session.add(instance)
                return instance, True
