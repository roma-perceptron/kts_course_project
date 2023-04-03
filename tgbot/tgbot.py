# all about telegram bot logics

import asyncio
import json
import os
import typing
from asyncio import Task
from typing import Optional
from aiohttp import ClientSession, TCPConnector

from tgbot.scheme.state_machine_scheme import BOT_COMMANDS_AND_STATES

BOT_COMMANDS = [
    {"command": cmd["command"], "description": cmd["description"]}
    for cmd in BOT_COMMANDS_AND_STATES
    if cmd["command"].startswith("/")
]
BOT_STATE_ACTIONS = {
    cmd["command"]: cmd["action"] for cmd in BOT_COMMANDS_AND_STATES
}
BOT_COMMAND_NAMES = [cmd["command"] for cmd in BOT_COMMANDS]

TOKEN = os.environ.get("TG_BOT_TOKEN", "")


if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application
    from kts_backend.store import BotAccessor


class TGBot:
    def __init__(self, token: str = TOKEN, timeout: int = 10):
        self.token: str = token
        self.base_url: str = f"https://api.telegram.org/bot{self.token}/"
        self.session = ClientSession(connector=TCPConnector())  # ssl=False
        self.timeout: int = timeout
        self.loop: Optional[asyncio.BaseEventLoop] = None
        self.bot_name = "@rp_kts_course_project_bot"
        self.base_chat_id = "-1001938935834"

    def build_query(self, method: str, params: dict):
        url = self.base_url + method + "?"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _send_action(
        self, method: Optional[str], params: dict, sleep: int = 1
    ):
        params["action"] = "typing"
        query_link = self.build_query("sendChatAction", params)
        async with self.session.get(query_link) as resp:
            await resp.json()
        await asyncio.sleep(sleep)  # спорно, ага..

    async def query(self, method: str, params: Optional[dict] = dict):
        if params.get("chat_id", False):
            await self._send_action(method, {"chat_id": params["chat_id"]})
        query_link = self.build_query(method, params)
        async with self.session.get(query_link) as resp:
            data = await resp.json()
            return data

    async def set_commands(self, *args):
        await self.query(
            "setMyCommands", {"commands": json.dumps(BOT_COMMANDS)}
        )

    # async def set_commands__sync(self, *args):
    #     query_link = self.build_query(
    #         "setMyCommands", {"commands": json.dumps(BOT_COMMANDS)}
    #     )
    #     import requests
    #     res = requests.get(query_link)


class Poller(TGBot):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.is_running: bool = False
        self.poll_task: Optional[Task] = None
        self.offset: int = 0
        #
        self.app.on_startup.append(self.start)
        self.app.on_startup.append(self.set_commands)
        self.app.on_cleanup.append(self.stop)

    async def start(self, *args, **kwargs):
        self.loop = asyncio.get_event_loop()
        print("event loop is running?", self.loop.is_running())
        self.is_running = True
        try:
            self.poll_task = asyncio.create_task(self.long_polling())
        except Exception as exp:
            print("wow! exp 1", exp)
            print("*" * 33)
            raise ZeroDivisionError
        print(" " * 3, "app.bot.start - ok")

    async def stop(self, *args, **kwargs):
        await self.session.close()
        self.is_running = False
        self.poll_task.cancel()

    async def long_polling(self):
        while self.is_running:
            try:
                await self._polling()
            except Exception as exp:
                print("wow! exp 2", exp)
                print("*" * 33)
                raise exp

    async def _polling(self):
        try:
            updates = await self.query(
                "getUpdates", {"offset": self.offset, "timeout": self.timeout}
            )
        except Exception as exp:
            print("wow! exp 3", exp)
            print("*" * 33)
            raise exp
        # print(
        #     "updates:",
        #     updates.get("ok", "FAIL"),
        #     len(updates.get("result", [])),
        #     updates,
        # )
        if updates.get("result", []):
            self.offset = updates["result"][-1]["update_id"] + 1
            #
            for update in updates["result"]:
                # put each update to the queue..
                # print(" " * 3, "[P]", update)
                await self.app.updates_queue.put(update)
                break


class Sender(TGBot):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        #
        self.app.on_startup.append(self.start)
        self.app.on_cleanup.append(self.stop)

    async def send_message(self, **kwargs):
        await self.query("sendMessage", kwargs)

    async def process_answer(self):
        while True:
            answer = await self.app.answers_queue.get()
            # print(" " * 3, "[A]", answer)
            if answer and answer.get("text", False):
                await self.send_message(**answer)
            #
            self.app.answers_queue.task_done()

    async def start(self, *args, **kwargs):
        self.is_running = True
        self.task = asyncio.create_task(self.process_answer())
        #
        await self.app.answers_queue.join()
        print(" " * 3, "app.sender.start - ok")

    async def stop(self, *args, **kwargs):
        await self.session.close()
        self.is_running = False
        self.task.cancel()


class StateMachine(TGBot):
    def __init__(self, app: "Application", accessor: "BotAccessor"):
        super().__init__()
        self.app = app
        self.accessor = accessor

    async def send_message(self, **kwargs):
        await self.query("sendMessage", kwargs)

    async def process(self, data):
        text = data["message"]["text"].replace(self.bot_name, "")
        # сначала проверка на ввод команды
        if text in BOT_COMMAND_NAMES:
            kwargs_for_reply = await BOT_STATE_ACTIONS[text](self, data)
        # затем - на наличие состояния
        elif data.get("bot_state", None):
            kwargs_for_reply = await BOT_STATE_ACTIONS[data["bot_state"]](
                self, data
            )
        # если ничего из этого - туповатое эхо/игнор
        else:
            # kwargs_for_reply = {'text': data["message"]["text"] + "?"}
            data["bot_state"] = "ignore"
            kwargs_for_reply = await BOT_STATE_ACTIONS[data["bot_state"]](
                self, data
            )

        kwargs_for_reply.update({"chat_id": data["message"]["chat"]["id"]})
        return kwargs_for_reply
