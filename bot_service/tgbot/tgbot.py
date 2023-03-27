# all about telegram bot logics

import asyncio
import os
from asyncio import Task
from typing import Optional, TYPE_CHECKING
from aiohttp import ClientSession, TCPConnector

if TYPE_CHECKING:
    from web.app import Application

TOKEN = os.environ.get("TG_BOT_TOKEN", "")


class TGBot:
    def __init__(self, token: str = TOKEN, timeout: int = 10):
        self.token: str = token
        self.base_url: str = f"https://api.telegram.org/bot{self.token}/"
        self.session = ClientSession(connector=TCPConnector())
        self.timeout: int = timeout

    def build_query(self, method: str, params: dict):
        url = self.base_url + method + "?"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url


class Poller(TGBot):
    def __init__(self, updates_queue: Optional[asyncio.Queue] = None):
        super().__init__()
        self.is_running: bool = False
        self.poll_task: Optional[Task] = None
        self.offset: int = 0
        self.updates_queue: Optional[asyncio.Queue] = updates_queue

    async def start(self, _: "Application"):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.long_polling())

    async def stop(self, app: "Application"):
        self.is_running = False
        await self.poll_task
        app.logger.warning(f"{self.__class__.__name__} is stopped")

    async def long_polling(self):
        while self.is_running:
            await self._polling()

    async def _polling(self):
        async with self.session.get(
                self.build_query(
                    "getUpdates", {"offset": self.offset, "timeout": self.timeout}
                )
        ) as resp:
            updates = await resp.json()
            print(
                "updates:",
                updates.get("ok", "FAIL"),
                len(updates.get("result", [])),
            )
            if updates.get("result", []):
                self.offset = updates["result"][-1]["update_id"] + 1
                #
                for update in updates["result"]:
                    # put each update to the queue..
                    print(" " * 3, "[P]", update)
                    await self.updates_queue.put(update)
                    break


class Sender(TGBot):
    def __init__(self, answers_queue: Optional[asyncio.Queue] = None):
        super().__init__()
        self.answers_queue: Optional[asyncio.Queue] = answers_queue
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None

    async def send_message(
            self, msg: Optional[str] = "Yeah!", chat_id: Optional[int] = None
    ):
        async with self.session.get(
                self.build_query("sendMessage", {"text": msg, "chat_id": chat_id})
        ) as resp:
            await resp.json()

    async def process_answer(self):
        while True:
            answer = await self.answers_queue.get()
            print(" " * 3, "[A]", answer)
            await self.send_message(**answer)
            #
            self.answers_queue.task_done()

    async def start(self, _: "Application"):
        self.is_running = True
        self.task = asyncio.create_task(self.process_answer())
        #
        await self.answers_queue.join()

    async def stop(self, app: "Application"):
        # TODO: Здесь описываешь процесс корректной остановки
        app.logger.warning(f"{self.__class__.__name__} НАПИШИ процесс корректной остановки")
class Getter__DEPRECATED(TGBot):
    def __init__(self):
        super().__init__()

    async def get_members(self, chat_id: str = "-1001938935834"):
        async with self.session.get(
                self.build_query("getChat", {"chat_id": chat_id})
        ) as resp:
            data = await resp.json()
        return data
