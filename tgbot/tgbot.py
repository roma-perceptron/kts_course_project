# all about telegram bot logics

import asyncio
import os
import typing
from asyncio import Task
from typing import Optional
from aiohttp import ClientSession, TCPConnector

TOKEN = os.environ.get("TG_BOT_TOKEN", "")


if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


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
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.is_running: bool = False
        self.poll_task: Optional[Task] = None
        self.offset: int = 0
        #
        self.app.on_startup.append(self.start)
        # app.on_cleanup.append(self.stop)

    async def start(self, *args, **kwargs):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.long_polling())
        print(' '*3, 'app.bot.start - ok')

    async def stop(self, *args, **kwargs):
        self.is_running = False
        await self.poll_task

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
                updates
            )
            if updates.get("result", []):
                self.offset = updates["result"][-1]["update_id"] + 1
                #
                for update in updates["result"]:
                    # put each update to the queue..
                    print(" " * 3, "[P]", update)
                    await self.app.updates_queue.put(update)
                    # self.app.updates_queue.put_nowait(update)
                    break


class Sender(TGBot):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        #
        app.on_startup.append(self.start)
        # app.on_cleanup.append(self.stop)

    async def send_message(
        self, msg: Optional[str] = "Yeah!", chat_id: Optional[int] = None
    ):
        async with self.session.get(
            self.build_query("sendMessage", {"text": msg, "chat_id": chat_id})
        ) as resp:
            await resp.json()

    async def process_answer(self):
        while True:
            answer = await self.app.answers_queue.get()
            print(" " * 3, "[A]", answer)
            await self.send_message(**answer)
            #
            self.app.answers_queue.task_done()

    async def start(self, *args, **kwargs):
        self.is_running = True
        self.task = asyncio.create_task(self.process_answer())
        #
        await self.app.answers_queue.join()
        print(' '*3, 'app.sender.start - ok')

    async def stop(self, *args, **kwargs):
        self.is_running = False
        await self.task


class Getter__DEPRECATED(TGBot):
    def __init__(self):
        super().__init__()

    async def get_members(self, chat_id: str = "-1001938935834"):
        async with self.session.get(
            self.build_query("getChat", {"chat_id": chat_id})
        ) as resp:
            data = await resp.json()
        return data
