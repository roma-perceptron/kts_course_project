import json
import typing
import random

from kts_backend.utils import dict_to_readable_text

if typing.TYPE_CHECKING:
    from tgbot.tgbot import StateMachine

"""
    sm ниже - это экземпляр класса StateMachine который пробрасывает себя сюда из менеджера
"""


async def example(sm: "StateMachine", data: dict):
    msg = "just empty example.."
    return msg


async def get_players(sm: "StateMachine", data: dict):
    players = await sm.accessor.get_all_players()
    msg = dict_to_readable_text(players)
    return {"text": msg}


async def make_fake_game(sm: "StateMachine", data: dict):
    msg = await sm.accessor.make_fake_game()
    return {"text": msg}


async def get_last_game(sm: "StateMachine", data: dict):
    game_data = await sm.accessor.get_last_game(chat_id=sm.base_chat_id)
    msg = dict_to_readable_text(game_data.to_serializable())
    return {"text": msg}


def generate_random_emoji():
    code_point = random.randint(0x1F900, 0x1F9FF)
    emoji = "\\U" + format(code_point, "X").zfill(8)
    return emoji.encode("utf-8").decode("unicode_escape")


async def _send_launch_button(sm: "StateMachine", data: dict):
    reply_markup = {
        "keyboard": [
            [{"text": "Запустить игру!", "callback_data": "launch_game"}]
        ],
        "one_time_keyboard": True,
        "selective": True,
    }
    #
    kwarg_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"@{data['message']['from']['username']} Когда участников будет достаточно, запускай игру!",
        "reply_markup": json.dumps(reply_markup),
        # 'reply_to_message_id': data['message']['message_id'],
    }
    res = await sm.app.sender.query("sendMessage", kwarg_for_reply)


async def await_launch(sm: "StateMachine", data: dict):
    kwarg_for_reply = {
        "chat_id": data["chat_id"],
        "text": "Дамы и Господа!\nИгра начинается!",
        "reply_markup": json.dumps({"remove_keyboard": True}),
    }
    return kwarg_for_reply


async def launch_game(sm: "StateMachine", data: dict):
    kwarg_for_reply = {
        "chat_id": data["chat_id"],
        "text": "Дамы и Господа!\nИгра начинается!",
        "reply_markup": json.dumps({"remove_keyboard": True}),
    }
    return kwarg_for_reply


async def start_team(sm: "StateMachine", data: dict):
    # проверить нет ли текущей команды в этом чате..
    if not current_team(sm, data):
        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": generate_random_emoji()
                        + " "
                        + data["message"]["from"]["first_name"],
                        "callback_data": "ignore",
                    },
                ],
                [
                    {
                        "text": "Присоединиться к команде",
                        "callback_data": "join_team",
                    },
                ],
            ],
        }
        #
        kwarg_for_reply = {
            "text": "Отлично!\nНачинаем новую игру\nНам нужно еще несколько участников, ждем их",
            "reply_markup": json.dumps(reply_markup),
        }
        #
        sm.app.user_states[data["user_chat_id"]] = "await_coplayers"
        sm.app.current_teams[data["chat_id"]] = [data["user_id"]]
        await _send_launch_button(sm, data)
    else:
        if user_in_team(sm, data):
            msg = "В уже в команде! Ждем еще участников и начинаем!"
        else:
            sm.app.current_teams[data["chat_id"]].append(data["user_id"])
            msg = "В этом чате уже начали создавать команду, добавил Вас"
        kwarg_for_reply = {"text": msg}
    return kwarg_for_reply


async def await_coplayers(sm: "StateMachine", data: dict):
    if data["message"].get("reply_to_message", False):
        if data["message"]["text"] == "Запустить игру!":
            return await launch_game(sm, data)
    else:
        return {}


async def _edit_reply_buttons(sm: "StateMachine", data: dict):
    edited_markup = data["message"]["reply_markup"]
    edited_markup["inline_keyboard"][0].append(
        {
            "text": generate_random_emoji()
            + " @"
            + data["message"]["from"]["first_name"],
            "callback_data": "ignore",
        },
    )
    await sm.app.sender.query(
        "editMessageReplyMarkup",
        {
            "chat_id": data["chat_id"],
            "message_id": data["message"]["reply_id"],
            "reply_markup": json.dumps(edited_markup),
        },
    )


async def join_team(sm: "StateMachine", data: dict):
    if user_in_team(sm, data):
        msg = "Вы таки уже в команде!"
    else:
        sm.app.current_teams[data["chat_id"]].append(data["user_id"])
        msg = f"{data['message']['from'].get('first_name', 'Инкогнито..')} присоединяется к команде!"
        await _edit_reply_buttons(sm, data)
    return {"text": msg}


async def ignore(sm: "StateMachine", data: dict):
    return {}  # empty message


def current_team(sm: "StateMachine", data: dict):
    return sm.app.current_teams.get(data["chat_id"], False)


def user_in_team(sm: "StateMachine", data: dict):
    return data["user_id"] in current_team(sm, data)
