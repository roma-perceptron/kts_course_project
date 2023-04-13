import json
from hashlib import sha256
from random import randint
from typing import Optional, Union

# BOT_NAME = "@rp_kts_course_project_bot"
# FAKE_CHAT_ID = -1001938935834
# FAKE_PLAYERS = [
#     {
#         "update_id": 883412673,
#         "message": {
#             "message_id": 73,
#             "from": {
#                 "id": 1341029783,
#                 "is_bot": False,
#                 "first_name": "Рома1",
#                 "last_name": "Перцептрон1",
#                 "username": "roma_perceptron1",
#                 "language_code": "ru",
#             },
#             "chat": {
#                 "id": -1001938935834,
#                 "title": "Bot_testing",
#                 "type": "supergroup",
#             },
#             "date": 1679089454,
#             "text": "blow",
#         },
#     },
#     {
#         "update_id": 883412674,
#         "message": {
#             "message_id": 73,
#             "from": {
#                 "id": 1234567890,
#                 "is_bot": False,
#                 "first_name": "Рома2",
#                 "last_name": "Перцептрон2",
#                 "username": "roma_perceptron2",
#                 "language_code": "ru",
#             },
#             "chat": {
#                 "id": -1001938935834,
#                 "title": "Bot_testing",
#                 "type": "supergroup",
#             },
#             "date": 1679089455,
#             "text": "blow",
#         },
#     },
# ]


def dict_to_readable_text(data: Optional[Union[dict, list]]):
    return (
        json.dumps(data, indent="\t", ensure_ascii=False)
        .encode("utf8")
        .decode()
    )


def get_random_scores():
    first = randint(0, 100)
    second = 100 - first
    return first, second


def generate_random_emoji():
    code_point = randint(0x1F900, 0x1F9FF)
    emoji = "\\U" + format(code_point, "X").zfill(8)
    return emoji.encode("utf-8").decode("unicode_escape")


def logger(func):
    async def wrapper(*args, **kwargs):
        print('\n', f' start of {func.__name__} '.center(100, '-'))
        try:
            sm, data = args[0], args[1]
            print(' '*3, 'current_game:', sm.app.current_games.get(data["chat_id"], False))
            print(' '*3, 'current_team:', sm.app.current_teams.get(data["chat_id"], []))
            print(' '*3, 'current_timers:', [t for t in sm.app.timer_schedule if t["chat_id"] != data["chat_id"]])
        except:
            pass
        func_result = await func(*args, **kwargs)
        print(' '*3, 'result:', func_result)
        print('\n', f' end of {func.__name__} '.center(100, '-'))
        #
        return func_result
    #
    return wrapper


def hash_it(secret: str):
    hash_object = sha256(bytes(secret, 'utf=8'))
    hex_dig = hash_object.hexdigest()
    return hex_dig
