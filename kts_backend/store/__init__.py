import asyncio
import typing

from kts_backend.store.database.database import Database
from kts_backend.store.bot.manager import BotManager
from kts_backend.store.bot.accessor import BotAccessor


if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        # from kts_backend.users.accessor import UserAccessor
        # self.user = UserAccessor(self)
        pass


def setup_store(app: "Application"):
    pass
