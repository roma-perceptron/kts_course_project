from typing import Optional
from aiohttp.web import Application as AiohttpApplication

from store.database.database import Database
from store.bot.manager import BotManager
from store import setup_store, Store
from tgbot.tgbot import Poller, Sender
from web.logger import setup_logging
from web.settings import Settings


class Application(AiohttpApplication):
    config = None
    settings: Optional["Settings"] = None
    store: Optional["Store"] = None
    database: Optional[Database] = None
    manager: Optional[BotManager] = None
    bot: Optional["Poller"] = None
    sender: Optional["Sender"] = None


app = Application()


async def setup_app() -> Application:
    app.settings = Settings()
    setup_logging(app)
    setup_store(app)
    return app
