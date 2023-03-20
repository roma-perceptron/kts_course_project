import asyncio
import json
from asyncio import Task
from typing import Optional
from random import randint

from kts_backend.store.bot.accessor import BotAccessor


BOT_NAME = "@rp_kts_course_project_bot"
FAKE_CHAT_ID = -1001938935834
FAKE_PLAYERS = [
    {
        "update_id": 883412673,
        "message": {
            "message_id": 73,
            "from": {
                "id": 1341029783,
                "is_bot": False,
                "first_name": "Рома1",
                "last_name": "Перцептрон1",
                "username": "roma_perceptron1",
                "language_code": "ru",
            },
            "chat": {
                "id": -1001938935834,
                "title": "Bot_testing",
                "type": "supergroup",
            },
            "date": 1679089454,
            "text": "blow",
        },
    },
    {
        "update_id": 883412674,
        "message": {
            "message_id": 73,
            "from": {
                "id": 1234567890,
                "is_bot": False,
                "first_name": "Рома2",
                "last_name": "Перцептрон2",
                "username": "roma_perceptron2",
                "language_code": "ru",
            },
            "chat": {
                "id": -1001938935834,
                "title": "Bot_testing",
                "type": "supergroup",
            },
            "date": 1679089455,
            "text": "blow",
        },
    },
]


def get_random_scores():
    first = randint(0, 100)
    second = 100 - first
    return first, second


class BotManager:
    def __init__(
        self,
        updates_queue: Optional[asyncio.Queue] = None,
        answers_queue: Optional[asyncio.Queue] = None,
        accessor: Optional[BotAccessor] = None,
    ):
        self.is_running: bool = False
        self.updates_queue: Optional[asyncio.Queue] = updates_queue
        self.answers_queue: Optional[asyncio.Queue] = answers_queue
        self.task: Optional[Task] = None
        self.accessor: BotAccessor = accessor
        self.BOT_COMMANDS = {
            "/help": "Help! I need somebody! Not just anybody!",
            "/game": "Начнем новую игру как только научимся это делать!",
            "/stop": "Стоп-игра!",
        }

    @staticmethod
    def is_command(text):
        pass

    async def make_echo_answer(self, data):
        text = data["message"]["text"].replace(BOT_NAME, "")
        #
        if text == "/fake_game":
            msg = await self._make_fake_game()
        elif text == "/get_game":
            game_data = await self.accessor.get_last_game(chat_id=FAKE_CHAT_ID)
            msg = (
                json.dumps(
                    game_data.to_serializable(), indent="\t", ensure_ascii=False
                )
                .encode("utf8")
                .decode()
            )
        elif text == "/get_players":
            players = await self.accessor.get_all_players()
            msg = (
                json.dumps(players, indent="\t", ensure_ascii=False)
                .encode("utf8")
                .decode()
            )
        else:
            msg = self.BOT_COMMANDS.get(
                data["message"]["text"].replace(BOT_NAME, ""),
                data["message"]["text"] + "?",
            )
        #
        return {"msg": msg, "chat_id": data["message"]["chat"]["id"]}

    async def process_update(self):
        while True:
            update = await self.updates_queue.get()
            print(" " * 3, "[W]", update)
            #
            answer = await self.make_echo_answer(update)
            await self.answers_queue.put(answer)
            #
            self.updates_queue.task_done()

    async def start(self):
        self.is_running = True
        self.task = asyncio.create_task(self.process_update())
        #
        await self.updates_queue.join()

    async def _make_fake_game(self):
        game_id, player_ids = await self.accessor.create_game(
            chat_id=FAKE_CHAT_ID, players=FAKE_PLAYERS
        )
        await self.accessor.create_score(
            game_id=game_id,
            player_ids=player_ids,
            player_points=get_random_scores(),
        )
        return "Yeah, new fake game just created! Check the last game command.."
