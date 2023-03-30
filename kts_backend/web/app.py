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

from tgbot import setup_sender, setup_poller
from kts_backend.store import setup_store


# __all__ = ("ApiApplication",)


class Application(AiohttpApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None
        self.store = None
        self.database: Optional[Database] = None
        self.bot = None
        self.sender = None
        self.manager = None
        self.updates_queue = None
        self.answers_queue = None
        #
        self.user_states = {}
        self.current_teams = {}
        self.current_games = {}
        self.timer_schedule = []
        #
        self.on_startup.append(self.init_queues)

    async def init_queues(self, *args, **kwargs):
        self.updates_queue = asyncio.Queue()
        self.answers_queue = asyncio.Queue()
        print(" " * 3, "queues inited!")


app = Application()     # debug=True


async def setup_app() -> Application:
    print("start creating app..")

    # creating database
    app.database = Database(app)

    # creating Bot's poller and sender instances
    app.bot = setup_poller(app)
    app.sender = setup_sender(app)

    # creating Manager instance
    app.manager = BotManager(app)

    # all coros should start via call app.on_startup in each __init__
    print("preparing done:")
    #
    return app
