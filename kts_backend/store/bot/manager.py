import asyncio
import json
import typing
from asyncio import Task
from typing import Optional
from random import randint

from kts_backend.store.bot.accessor import BotAccessor
from kts_backend.utils import dict_to_readable_text

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


from tgbot.tgbot import StateMachine


class BotManager:
    def __init__(
        self,
        app: "Application",
    ):
        self.app = app
        self.is_running: bool = False
        self.task: Optional[Task] = None
        self.accessor: BotAccessor = BotAccessor(app.database)
        self.state_machine: StateMachine = StateMachine(self.app, self.accessor)
        self.BOT_COMMANDS = {
            "/help": "Help! \nI need somebody! \n(Help!) Not just anybody!",
            "/game": "Начнем новую игру как только научимся это делать!",
            "/stop": "Стоп-игра!",
        }
        #
        app.on_startup.append(self.start)
        # app.on_cleanup.append(self.stop)

    async def _check_callback(self, update: dict):
        # переупаковываю содержимое ответного сообщения, для совместимости
        # print(dict_to_readable_text(update))
        if update.get("callback_query", False):
            update = {
                "message": {
                    "from": update["callback_query"]["from"],
                    "chat": update["callback_query"]["message"]["chat"],
                    "text": update["callback_query"]["message"]["text"],
                    "reply_id": update["callback_query"]["message"][
                        "message_id"
                    ],
                    "reply_markup": update["callback_query"]["message"][
                        "reply_markup"
                    ],
                },
                "bot_state": update["callback_query"]["data"],
                "callback": True,
            }
        #
        return update

    async def _put_ids_on_top(self, update: dict):
        update["user_id"] = str(update["message"]["from"]["id"])
        update["chat_id"] = str(update["message"]["chat"]["id"])
        user_chat_id = ":".join([update["user_id"], update["chat_id"]])
        update["user_chat_id"] = user_chat_id

    async def _set_user_state(self, update: dict):
        if not update.get("callback", False):
            update["bot_state"] = self.app.user_states.get(
                update["user_chat_id"], None
            )

    #
    async def process_update(self):
        while True:
            update = await self.app.updates_queue.get()
            # print(" " * 3, "[W]", update)

            # переупаковка ответа, при необходимости
            update = await self._check_callback(update)
            # print('\nupdate:', update, '\n')

            # ставлю все айдишники на верхний уровень
            await self._put_ids_on_top(update)

            # проверяю state этого юзера и добавляю его к объекту update
            await self._set_user_state(update)

            answer = await self.state_machine.process(update)
            await self.app.answers_queue.put(answer)
            #
            self.app.updates_queue.task_done()

    async def start(self, *_: list, **__: dict):
        self.is_running = True
        self.task = asyncio.create_task(self.process_update())
        #
        await self.app.updates_queue.join()
        print(" " * 3, "app.manager.start - ok")
