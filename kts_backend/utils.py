import json
from random import randint
from typing import Optional

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


def dict_to_readable_text(data: Optional[dict]):
    return (
        json.dumps(data, indent="\t", ensure_ascii=False)
        .encode("utf8")
        .decode()
    )


def get_random_scores():
    first = randint(0, 100)
    second = 100 - first
    return first, second
