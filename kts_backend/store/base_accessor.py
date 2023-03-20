import typing
from logging import getLogger

from sqlalchemy.engine import ChunkedIteratorResult

# if typing.TYPE_CHECKING:
#     from app.web.app import Application


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

    async def execute_query(self, query, only_last: bool = False):
        async with self.database.session.begin() as session:
            result: ChunkedIteratorResult = await session.execute(query)
            if only_last:
                return result.fetchone()[0]
            else:
                return result.fetchall()

    async def execute_query_creation(self, model_with_params):
        async with self.database.session.begin() as session:
            session.add(model_with_params)
            await session.commit()
            # await session.rollback()
        return model_with_params
