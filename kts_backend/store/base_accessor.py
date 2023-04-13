import typing

from sqlalchemy import delete, select
from sqlalchemy.engine import ChunkedIteratorResult

from kts_backend.store.database import db

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class BaseAccessor:
    def __init__(self, app: 'Application'):
        self.app = app
        self.database = app.database

    async def execute_query(self, query, only_last=False, no_return=False):
        async with self.database.session.begin() as session:
            result: ChunkedIteratorResult = await session.execute(query)
            if not no_return:
                if only_last:
                    result = result.fetchone()[0]
                else:
                    result = result.fetchall()
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
