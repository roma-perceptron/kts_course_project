import asyncio
import datetime
import json
import pickle
import time
import typing
from asyncio import Task
from typing import Optional
from random import randint

from sqlalchemy import select

from kts_backend.game.models import CurrentParamsModel
from kts_backend.store.bot.accessor import BotAccessor
from kts_backend.utils import dict_to_readable_text

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

from tgbot import state_machine_functions
from tgbot.tgbot import StateMachine


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.is_running: bool = False
        self.task: Optional[Task] = None
        self.accessor: BotAccessor = BotAccessor(app.database)
        self.state_machine: StateMachine = StateMachine(self.app, self.accessor)
        self.timer_is_running: bool = False
        self.timer: Optional[Task] = None
        self.timer_delay: int = 1
        #
        self.app.on_startup.append(self.start)
        self.app.on_startup.append(self.start_timer)
        self.app.on_startup.append(self.load_current)
        self.app.on_cleanup.append(self.stop)
        self.app.on_cleanup.append(self.stop_timer)

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
        while self.is_running:
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

    async def start(self, *args, **kwargs):
        self.is_running = True
        self.task = asyncio.create_task(self.process_update())
        #
        await self.app.updates_queue.join()
        print(" " * 3, "app.manager.start - ok")

    async def stop(self, *args, **kwargs):
        await self.state_machine.session.close()
        self.is_running = False
        self.task.cancel()

    #
    # timer..
    async def check_timers(self):
        for timer_task in self.app.timer_schedule:
            if not timer_task["executed"]:
                if datetime.datetime.now() >= timer_task["time"]:
                    print(
                        "timer dzin!!!",
                        datetime.datetime.now(),
                        timer_task["type"],
                        timer_task["time"],
                    )
                    answer = await timer_task["command"](
                        self.state_machine, {"chat_id": timer_task["chat_id"]}
                    )
                    timer_task["executed"] = True
                    answer["chat_id"] = timer_task["chat_id"]
                    await self.app.answers_queue.put(answer)
        #
        # подчищаю..
        self.app.timer_schedule = [
            timer_task
            for timer_task in self.app.timer_schedule
            if not timer_task["executed"]
        ]

    async def timer_tick(self):
        while self.timer_is_running:
            await asyncio.sleep(self.timer_delay)
            await self.check_timers()

    async def start_timer(self, *args, **kwargs):
        self.timer_is_running = True
        self.timer = asyncio.create_task(self.timer_tick())
        #
        print(" " * 3, "app.manager.start_timer - ok")

    async def stop_timer(self, *args, **kwargs):
        self.timer_is_running = False
        self.timer.cancel()
        await self.timer

    #
    async def load_current(self, *args, **kwargs):
        try:
            data = await self.accessor.execute_query(
                select(CurrentParamsModel.current), only_last=True
            )
            current = pickle.loads(data)
        except Exception as exp:
            current = {}
        #
        self.app.user_states = current.get("states", {})
        self.app.current_teams = current.get("teams", {})
        self.app.current_games = current.get("games", {})
        self.app.timer_schedule = current.get("schedule", [])
        print("current params loaded ok", current)
