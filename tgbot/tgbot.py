# all about telegram bot logics

import asyncio
import json
import os
import typing
from asyncio import Task
from typing import Optional
from aiohttp import ClientSession, TCPConnector

from kts_backend.utils import dict_to_readable_text
from tgbot.scheme.state_machine_scheme import BOT_COMMANDS_AND_STATES


SHORT_DESCRIPTION = [
    'Бот для игры в "Что? Где? Когда?"',
    'Знатоки против chatGTP!',
]
TOTAL_DESCRIPTION = [
    'KTS COURSE PROJECT BOT',
    '',
    'Игра "Что? Где? Когда?", но вместо телезрителей - chatGTP. Нейросеть не только придумывает вопросы, но и проверяет ответы знатоков.',
    '',
    'Играть можно как в одиночку, так командой. Для этого добавьте бота в свою группу.',
    '',
    'Запускайте команду /start, присоединяйтесь к команде, играйте следуя инструкциям бота.',
    '',
    'Не слишком надейтесь на этот искусственный интеллект, он способен выдавать как некорректные вопросы, так и неверные ответы 😏',
]

HELP_DESCRIPTION = [
    'KTS COURSE PROJECT BOT',
    '',
    'Игра "Что? Где? Когда?", но вместо телезрителей - chatGTP. Нейросеть не только придумывает вопросы, но и проверяет ответы знатоков.',
    '',
    'Играть можно как в одиночку, так командой. Для этого добавьте бота в свою группу.',
    '',
    'Для начала игры кто-то должен вызвать команду /start. Далее все желающие присоединяются к игре и когда состав готов (так же может быть и один человек), тот кто стартовал игру ее же и запускает.',
    '',
    'После этого, случайным образом будет выбран капитан игры и начат первый раунд с первым вопросом. Игроки получают минуту времени на обсужжение, по истечении которой ведущий попросит капитана выбрать игрока который даст ответ. Так же можно будет ответить досрочно.',
    '',
    'Игрок которому капитан поручит ответ должен написать его в ответ на сообщение бота. На написание ответа так же отводится минута. Бот проверит ответ и сообщит свое решение, а так же промежуточный счет. Начнется следующий раунд.',
    '',
    'Игра идет до тех пока одна из сторон не наберет 6 очков, максимум 11 раундов.',
    '',
    'В процессе игры участники могут свободно обмениваться сообщениями в чате.',
    'Не слишком надейтесь на этот искусственный интеллект, он способен выдавать как некорректные вопросы, так и неверные ответы 😏',
]


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
    from kts_backend.store.bot.accessor import BotAccessor


class TGBot:
    def __init__(self, app: "Application", timeout: int = 10):
        self.app = app
        self.token: str = app.config.bot.token
        self.base_url: str = f"https://api.telegram.org/bot{self.token}/"
        self.session = ClientSession(connector=TCPConnector())  # ssl=False
        self.timeout: int = timeout
        self.loop: Optional[asyncio.BaseEventLoop] = None
        self.bot_name = '@' + self.app.config.bot.bot_name

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
        if params.get('text', False) and len(params['text']) > 4096:
            params['text'] = params['text'][:4000] + '..\n\n..message was truncated'
        query_link = self.build_query(method, params)
        async with self.session.get(query_link) as resp:
            data = await resp.json()
            return data

    async def set_commands(self, *args):
        await self.query(
            "setMyCommands", {"commands": json.dumps(BOT_COMMANDS)}
        )

    async def set_descriptions(self, *args):
        await self.query(
            'setMyDescription',
            {'description': '\n'.join(TOTAL_DESCRIPTION)}
        )
        await self.query(
            'setMyShortDescription',
            {'short_description': '\n'.join(SHORT_DESCRIPTION)}
        )

    # async def set_commands__sync(self, *args):
    #     query_link = self.build_query(
    #         "setMyCommands", {"commands": json.dumps(BOT_COMMANDS)}
    #     )
    #     import requests
    #     res = requests.get(query_link)


class Poller(TGBot):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.is_running: bool = False
        self.poll_task: Optional[Task] = None
        self.offset: int = 0
        #
        self.app.on_startup.append(self.start)
        self.app.on_startup.append(self.set_commands)
        self.app.on_startup.append(self.set_descriptions)
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
        super().__init__(app, *args, **kwargs)
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        #
        self.task_count: int = app.processor_count
        self.tasks: Optional[list[Task]] = []
        #
        self.app.on_startup.append(self.start)
        self.app.on_cleanup.append(self.stop)

    async def send_message(self, **kwargs):
        await self.query("sendMessage", kwargs)

    async def process_answer(self):
        while True:
            answer = await self.app.answers_queue.get()
            if answer and answer.get("text", False):
                await self.send_message(**answer)
            #
            self.app.answers_queue.task_done()

    async def start(self, *args, **kwargs):
        self.is_running = True
        for _ in range(self.task_count):
            self.tasks.append(asyncio.create_task(self.process_answer()))
            print(" " * 3, 'теперь task_count sender:', len(self.tasks))
        #
        await self.app.answers_queue.join()
        print(" " * 3, "app.sender.start - ok")

    async def stop(self, *args, **kwargs):
        await self.session.close()
        self.is_running = False
        for task in self.tasks:
            task.cancel()


class StateMachine(TGBot):
    def __init__(self, app: "Application", accessor: "BotAccessor"):
        super().__init__(app)
        self.accessor = accessor

    async def send_message(self, **kwargs):
        await self.query("sendMessage", kwargs)

    async def process(self, data):
        text = data.get('message', dict()).get('text', '').replace(self.bot_name, "")
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
            if self.app.debug:
                kwargs_for_reply = {'text': data["message"]["text"] + "?"}
            else:
                data["bot_state"] = "ignore"
                kwargs_for_reply = await BOT_STATE_ACTIONS[data["bot_state"]](
                    self, data
                )

        if not data.get('message', None):
            kwargs_for_reply.update({"chat_id": find_chat_id(data)})
        else:
            kwargs_for_reply.update({"chat_id": data["message"]["chat"]["id"]})
        #
        return kwargs_for_reply


def find_chat_id(data):
    chat_id = None
    for key in data:
        try:
            chat_id = data[key]['chat']['id']
            return chat_id
        except (KeyError, TypeError):
            continue
    #
    return chat_id
