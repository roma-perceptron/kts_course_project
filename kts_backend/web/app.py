import asyncio
import pickle

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)

# from pyparsing import Optional    # где это вообще используется или должно?
from chatgpt.chatgpt import MasterOfTheGame
from kts_backend import __appname__, __version__
from .config import setup_config
from .urls import register_urls

from typing import Optional
from kts_backend.store.database.database import Database
from kts_backend.store.bot.manager import BotManager
from kts_backend.admin.manager import AdminManager

from tgbot import setup_sender, setup_poller
from kts_backend.api.routes import setup_routes
from kts_backend.web.mw import setup_middlewares
from kts_backend.store import setup_store

from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage


# __all__ = ("ApiApplication",)

from ..game.models import CurrentParamsModel


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
        self.processor_count = None
        self.admin_manager: Optional[AdminManager] = None
        self.gtp_master = None
        #
        self.user_states = {}
        self.current_teams = {}
        self.current_games = {}
        self.timer_schedule = []
        #
        self.on_startup.append(self.init_queues)
        self.on_shutdown.append(self.save_current)

    async def init_queues(self, *args, **kwargs):
        self.updates_queue = asyncio.Queue()
        self.answers_queue = asyncio.Queue()
        print(" " * 3, "queues inited!")

    async def save_current(self, *args, **kwargs):
        await self.manager.accessor.clear_table(CurrentParamsModel)
        await self.manager.accessor.execute_query_creation(
            CurrentParamsModel(
                current=pickle.dumps(
                    {
                        "states": self.user_states,
                        "teams": self.current_teams,
                        "games": self.current_games,
                        "schedule": self.timer_schedule,
                    }
                )
            )
        )
        print("current params saved ok")


class Request(AiohttpRequest):
    # admin: Optional[Admin] = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self):
        return self.request.app.database

    @property
    def manager(self):
        return self.request.app.manager

    @property
    def admin_manager(self):
        return self.request.app.admin_manager


app = Application(debug=False)  # debug=True


async def setup_app(config_path: str, processor_count: int = 1) -> Application:
    print("start creating app..")
    app.processor_count = processor_count

    #
    setup_config(app, config_path)
    #
    setup_routes(app)
    session_setup(app, EncryptedCookieStorage(app.config.session.key))
    setup_aiohttp_apispec(
        app,
        title="Roma Perceptron: ЧГК + chatGTP tg-Bot",
        url="/docs/json",
        swagger_path="/docs",
    )

    # creating database
    app.database = Database(app)

    # creating Bot's poller and sender instances
    app.bot = setup_poller(app)
    app.sender = setup_sender(app)

    # creating Manager instance
    app.manager = BotManager(app)

    # prepare chatGTP client
    app.gtp_master = MasterOfTheGame(config=app.config.openai)

    # creating Admin Manager and first admin
    app.admin_manager = AdminManager(app)

    # мидлвары..
    setup_middlewares(app)

    print("preparing done:")

    #
    return app
