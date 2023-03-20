import asyncio
from typing import Sequence, Callable

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)

# from pyparsing import Optional    # где это вообще используется или должно?

from kts_backend import __appname__, __version__
from .urls import register_urls

from typing import Optional
from kts_backend.store.database.database import Database
from kts_backend.store.bot.manager import BotManager
from kts_backend.store.bot.accessor import BotAccessor

from tgbot import setup_bot
from kts_backend.store import setup_store


# __all__ = ("ApiApplication",)


class Application(AiohttpApplication):
    config = None
    store = None
    database: Optional[Database] = None


app = Application()


async def setup_app() -> Application:
    print("start creating app..")
    database = setup_store()
    await database.connect()

    # creating queues
    updates_queue = asyncio.Queue()
    answers_queue = asyncio.Queue()

    # creating Bot's poller and sender instances
    bot, sender = setup_bot(updates_queue, answers_queue)

    # creating Manager instance
    manager = BotManager(updates_queue, answers_queue, BotAccessor(database))

    # starting coroutines
    await bot.start()
    await manager.start()
    await sender.start()

    #
    app.database = database
    app.bot = bot
    app.sender = sender
    app.manager = manager
    # print('here are app:', type(app), app.__dict__)
    return app
