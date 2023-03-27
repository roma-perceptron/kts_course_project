from asyncio import Queue
from typing import TYPE_CHECKING

from store.bot.accessor import BotAccessor
from store.bot.manager import BotManager
from store.database.database import Database
from tgbot.tgbot import Poller, Sender

if TYPE_CHECKING:
    from web.app import Application


class Store:
    def __init__(self, app: "Application"):
        updates_queue = Queue()
        answers_queue = Queue()

        app.bot = Poller(updates_queue=updates_queue)
        app.sender = Sender(answers_queue=answers_queue)
        app.manager = BotManager(updates_queue, answers_queue, BotAccessor(app.database))
        # запуск сервисов и служб
        app.on_cleanup.append(app.bot.start)
        app.on_cleanup.append(app.manager.start)
        app.on_cleanup.append(app.sender.start)
        # завершение сервисов и служб
        app.on_cleanup.append(app.bot.stop)
        app.on_cleanup.append(app.manager.stop)
        app.on_cleanup.append(app.sender.stop)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.store = Store(app)
