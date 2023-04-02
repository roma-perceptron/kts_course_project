import asyncio
import json
import random
import typing
import uuid

from datetime import datetime, timedelta

from kts_backend.utils import dict_to_readable_text, generate_random_emoji
from kts_backend.game.dataclasses import QuestionDC, PlayerDC
from kts_backend.game.models import QuestionModel, UsedQuestionModel

from kts_backend.game.models import QuestionModel
from chatgpt.chatgpt import gpt_master, get_theme
from openai.error import APIConnectionError

from sqlalchemy.exc import DBAPIError

if typing.TYPE_CHECKING:
    from tgbot.tgbot import StateMachine

NUMBER_ROUNDS = 3
WIN_SCORE = NUMBER_ROUNDS // 2 + 1
TIME_TO_THINKING = 15
TIME_TO_ANSWER = 60
TIME_BETWEEN_ROUNDS = 5
POINTER = "\U0001F449" + " "

FAKE_QUESTION = QuestionDC(
    question="Почему сосиски продаются по 10 штук в пачке, а хот-доги по 9?",
    answers=["42", "ave ChatGPT", "потому что гладиолус!"],
    context="Тупой вопрос",
    story="В 1786 году, в кафе на берегу Женевского озера встретились два видных представителя..",
)

"""
    sm ниже - это экземпляр класса StateMachine который пробрасывает себя сюда из менеджера
"""


async def example(sm: "StateMachine", data: dict):
    msg = "just empty example.."
    return msg


async def _send_launch_button(sm: "StateMachine", data: dict):
    reply_markup = {
        "keyboard": [[{"text": "Запустить игру!"}]],
        "selective": True,
    }
    #
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"@{data['message']['from']['username']} Когда участников будет достаточно, запускай игру!",
        "reply_markup": json.dumps(reply_markup),
    }
    await sm.app.sender.query("sendMessage", kwargs_for_reply)


async def await_launch(sm: "StateMachine", data: dict):
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": "Дамы и Господа!\nИгра начинается!",
        "reply_markup": json.dumps({"remove_keyboard": True}),
    }
    return kwargs_for_reply


async def _send_round_caption(sm: "StateMachine", data: dict):
    game = current_game(sm, data)
    #
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"Начинаем {len(game['rounds']) + 1}-й раунд!",
    }
    await sm.app.sender.query("sendMessage", kwargs_for_reply)
    return game


async def _send_question(sm, data, question: QuestionDC):
    # сначала закидываем историю
    kwargs_for_reply = {"chat_id": data["chat_id"], "text": question.story}
    await sm.app.sender.query("sendMessage", kwargs_for_reply)
    await asyncio.sleep(1)  # 5sec

    # теперь сам вопрос
    kwargs_for_reply["text"] = question.question
    await sm.app.sender.query("sendMessage", kwargs_for_reply)
    await asyncio.sleep(1)  # 2


async def start_round(sm: "StateMachine", data: dict):
    await asyncio.sleep(1)

    # сообщение о раунде
    game = await _send_round_caption(sm, data)

    # проверяем есть ли вопрос в запасе, если нет - генерим его
    # game['next_questions'] = []
    if game["next_questions"]:
        question = game["next_questions"].pop()
    else:
        await sm.app.sender.query(
            "sendMessage",
            {
                "chat_id": data["chat_id"],
                "text": "Мне нужно немного времени чтобы сформулировать вопрос..",
            },
        )
        new_questions = await get_new_questions(sm, data)
        question = random.choice(new_questions)

    # формируем и задаем вопрос
    game_round = {
        # 'question': game['next_questions'].pop(),
        "question": question,
        "team_answer": "",
        "score": 0,
    }
    game["rounds"].append(game_round)
    await _send_question(sm, data, game_round["question"])

    # добавляю в расписание таймер и начинается отсчет времени
    sm.app.timer_schedule.append(
        {
            "time": datetime.now() + timedelta(seconds=TIME_TO_THINKING),
            "chat_id": data["chat_id"],
            "command": continue_round,
            "executed": False,
            "type": "continue_round",
        }
    )
    await send_button_for_early_answer(sm, data)    # кнопка досрочного ответа капитану
    return {"text": "У вас минута на обсуждение!"}


async def send_button_for_early_answer(sm: "StateMachine", data: dict):
    reply_markup = {
        "keyboard": [[{"text": "Досрочный ответ"}]],
        "selective": True,
    }
    captain = current_team(sm, data)[0]
    captain_uci = f"{captain['user_id']}:{data['chat_id']}"
    sm.app.user_states[captain_uci] = 'ready_for_early_answer'
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"@{captain['username']} Если готовы отвечать - жмите кнопку",
        "reply_markup": json.dumps(reply_markup),
    }
    await sm.app.sender.query('sendMessage', kwargs_for_reply)
    return {}


async def ready_for_early_answer(sm: "StateMachine", data: dict):
    for timer in sm.app.timer_schedule:
        if (
            timer["chat_id"] == data["chat_id"]
            and timer["type"] == "continue_round"
        ):
            timer["executed"] = True
    #
    captain = current_team(sm, data)[0]
    captain_uci = f"{captain['user_id']}:{data['chat_id']}"
    sm.app.user_states[captain_uci] = 'ignore'
    await early_answer(sm, data)
    return {}




async def _checkout_score(game: dict):
    wisemans_score = sum(game_round["score"] for game_round in game["rounds"])
    chatgpts_score = len(game["rounds"]) - wisemans_score
    #
    if wisemans_score > chatgpts_score:
        winners = "Знатоки ведут!"
    elif chatgpts_score > wisemans_score:
        winners = "ChatGPT ведет!"
    else:
        winners = "Равный счет!"

    score = (wisemans_score, chatgpts_score)
    return f"Счет {wisemans_score}:{chatgpts_score}, {winners}", score


def _format_answer(answer: str):
    return answer.lower().strip()


async def _check_answer(sm: "StateMachine", data: dict, answer: str):
    game = current_game(sm, data)
    game_round = game["rounds"][-1]

    win = False
    f_answers = list(map(_format_answer, game_round["question"].answers))
    if answer.lower().strip() in f_answers:
        win = True
    else:
        if answer:
            await sm.app.sender.query(
                "sendMessage",
                {
                    "chat_id": data["chat_id"],
                    "text": "Хм.. надо спросить что о таком ответе думает chatGPT..",
                },
            )
            await sm.app.sender._send_action(
                method=None, params={"chat_id": data["chat_id"]}, sleep=0
            )
            win = await gpt_master.check_answer(game_round["question"], answer)
    #
    if win:
        game_round["score"] = 1
        result = "И это правильный ответ!"
    else:
        if answer:
            result = "К сожалению, я не могу принять этот ответ."
        else:
            result = "Печально что Вы даже не попробовали выдвинуть версию.."
        result += "\n\nПравильный ответ: "
        result += " или ".join(game_round["question"].answers)
    #
    score_str, score = await _checkout_score(game)

    #
    return result + "\n\n" + score_str, score


async def await_answer(sm: "StateMachine", data: dict):
    if not current_game(sm, data):
        return {}
    #
    answer = data.get("message", {}).get("text", "")

    # надо выключить таймер, найдя его
    for timer in sm.app.timer_schedule:
        if (
            timer["chat_id"] == data["chat_id"]
            and timer["type"] == "await_answer"
        ):
            timer["executed"] = True

    # сначала повтор ответа
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"Ваш ответ: {answer}"
        if answer
        else "Вы не дали ответа в течении минуты",
        "reply_markup": json.dumps({"remove_keyboard": True})
        if not answer
        else None,
    }
    await sm.app.sender.query("sendMessage", kwargs_for_reply)

    # затираю состояния у всех юзеров текущей группы.. перезаписываю?
    sm.app.user_states = {
        user_chat_id: state
        for user_chat_id, state in sm.app.user_states.items()
        if user_chat_id.split(":")[1] != data["chat_id"]
    }

    # запись в базу данные о сыгранном вопросе
    current_question = current_game(sm, data)["rounds"][-1]["question"]
    result = await sm.accessor.add_questions_to_used(
        current_question, data["chat_id"], current_team(sm, data)
    )
    await sm.accessor.mark_as_non_virgin([current_question.id_db])

    # теперь собственно отработка ответа (даже если он пустой == неправильный)
    result, score = await _check_answer(sm, data, answer)
    if (
        sum(score) == NUMBER_ROUNDS
        or score[0] == WIN_SCORE
        or score[1] == WIN_SCORE
    ):
        await sm.accessor.update_or_create_current_game(
            data["chat_id"], current_game(sm, data)["rounds"]
        )

        result += "\n\nНа этом игра закончена, всем спасибо, все свободны!"
        # здесь еще надо сохранить все в БД..
        sm.app.current_games.pop(data["chat_id"])
        sm.app.current_teams.pop(data["chat_id"])
        sm.app.timer_schedule = [
            tt
            for tt in sm.app.timer_schedule
            if tt["chat_id"] != data["chat_id"]
        ]
    else:
        # добавляю в расписание таймер для запуска следующего раунда
        sm.app.timer_schedule.append(
            {
                "time": datetime.now() + timedelta(seconds=TIME_BETWEEN_ROUNDS),
                "chat_id": data["chat_id"],
                "command": start_round,
                "executed": False,
                "type": "start_round",
            }
        )
    #
    kwargs_for_reply = {"text": result, "chat_id": data["chat_id"]}
    return kwargs_for_reply


async def await_choose_player_who_answer(sm: "StateMachine", data: dict):
    if condition_for_quasi_callback(sm, data):
        if data["message"]["text"].startswith(POINTER):
            player_who_answer = (
                data["message"]["text"].replace(POINTER, "").strip()
            )
            kwargs_for_reply = {
                "chat_id": data["chat_id"],
                "text": "Капитан сделал свой выбор!",
                "reply_markup": json.dumps({"remove_keyboard": True}),
            }
            await sm.app.sender.query("sendMessage", kwargs_for_reply)

            #
            player_who_answer = [
                p
                for p in current_team(sm, data)
                if p["first_name"] == player_who_answer
            ][0]
            # ТУТ ЕСТЬ МЕСТО ДЛЯ КОСЯКА: username может вовсе отсутствовать у юзера телеги
            kwargs_for_reply = {
                "chat_id": data["chat_id"],
                "text": f"@{player_who_answer['username']} я весь во внимании:",
                "reply_markup": json.dumps(
                    {"force_reply": True, "selective": True}
                ),
            }
            uci = f"{player_who_answer['user_id']}:{data['chat_id']}"
            sm.app.user_states[uci] = "await_answer"
            #
            return kwargs_for_reply
        else:
            return {}
    else:
        return {}


async def _choose_player_who_answer(sm: "StateMachine", data: dict):
    players = current_team(sm, data)
    if not players:
        return {}

    captain = players[0]
    #
    reply_markup = {
        "keyboard": [
            [{"text": POINTER + player.get("first_name", "?!")}]
            for player in players
        ],
        # "one_time_keyboard": True,
        "selective": True,
    }
    #
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"@{captain['username']} Кто будет отвечать на вопрос?",
        "reply_markup": json.dumps(reply_markup),
    }
    uci = f"{captain['user_id']}:{data['chat_id']}"
    sm.app.user_states[uci] = "await_choose_player_who_answer"
    await sm.app.sender.query("sendMessage", kwargs_for_reply)

    # добавляю таймер для ответа
    sm.app.timer_schedule.append(
        {
            "time": datetime.now() + timedelta(seconds=TIME_TO_ANSWER),
            "chat_id": data["chat_id"],
            "command": await_answer,
            "executed": False,
            "type": "await_answer",
        }
    )


async def continue_round(sm: "StateMachine", data: dict):
    # сообщение об окончании времени на размышление
    await sm.app.sender.query(
        "sendMessage",
        {"text": "Дамы и Господа, время вышло!", "chat_id": data["chat_id"]},
    )
    # сообщение капитану c просьбой выбрать отвечающего (капитан это первый в списке игроков команды)
    await _choose_player_who_answer(sm, data)
    return {}


async def early_answer(sm: "StateMachine", data: dict):
    # сообщение об готовности принять досрочный ответ
    await sm.app.sender.query(
        "sendMessage",
        {
            "text": "О, досрочный ответ!\nЭто прекрасно!",
            "chat_id": data["chat_id"],
            "reply_markup": json.dumps({"remove_keyboard": True}),
        },
    )
    # сообщение капитану c просьбой выбрать отвечающего (капитан это первый в списке игроков команды)
    await _choose_player_who_answer(sm, data)
    return {}


async def launch_game(sm: "StateMachine", data: dict):
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": "Дамы и Господа!\nИгра начинается!",
        "reply_markup": json.dumps({"remove_keyboard": True}),
    }
    await sm.app.sender.query("sendMessage", kwargs_for_reply)

    # назначение капитана: капитан это первый юзер в списке игроков команды
    team = current_team(sm, data)
    captain = random.choice(team)
    team.remove(captain)
    team.insert(0, captain)
    sm.app.current_teams[data["chat_id"]] = team
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"В этой игре капитаном будет {captain['first_name']}",
    }
    await sm.app.sender.query("sendMessage", kwargs_for_reply)

    await sm.accessor.update_or_create_current_game(data["chat_id"])

    # сбор вопросов из базы для раундов
    questions = await sm.accessor.get_questions_from_db__reused(
        count=NUMBER_ROUNDS,
        chat_id=data["chat_id"],
        user_ids=[user["user_id"] for user in team],
    )

    sm.app.current_games[data["chat_id"]] = {
        # 'team_id': uuid.uuid4(),
        "team_users": current_team(sm, data),
        "rounds": [],
        "next_questions": questions,
    }

    await sm.accessor.update_or_create_current_game(data["chat_id"])

    return await start_round(sm, data)


async def stop_game(sm: "StateMachine", data: dict):
    team = current_team(sm, data)
    if team:
        if team[0]["user_id"] == data["user_id"]:
            # удаляю данные об игре, о команде, о состоянии и таймеры (если были)
            sm.app.current_games.pop(data["chat_id"], None)
            sm.app.current_teams.pop(data["chat_id"], None)
            sm.app.user_states.pop(f"{data['user_id']}:{data['chat_id']}", None)
            sm.app.timer_schedule = [
                t
                for t in sm.app.timer_schedule
                if t["chat_id"] != data["chat_id"]
            ]
            text = "Готово! Можно начинать новую игру!"
        else:
            text = "Только капитан команды может отменить игру"
        #
        return {"text": text}
    else:
        return {"text": "Так вроде и не начато никакой игры в этом чате.."}


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
        kwargs_for_reply = {
            "text": "Отлично!\nНачинаем новую игру\nНам нужно еще несколько участников, ждем их",
            "reply_markup": json.dumps(reply_markup),
        }
        #
        sm.app.user_states[data["user_chat_id"]] = "await_coplayers"
        await sm.accessor.create_new_team(data["chat_id"])
        await add_player_to_team(sm, data)
        await _send_launch_button(sm, data)
    else:
        if user_in_team(sm, data):
            msg = "Вы уже в команде! Ждем еще участников и начинаем!"
        else:
            await add_player_to_team(sm, data)
            msg = "В этом чате уже начали создавать команду, добавил Вас"
        kwargs_for_reply = {"text": msg}
    return kwargs_for_reply


async def add_player_to_team(sm: "StateMachine", data: dict):
    player_data = {
        "user_id": data["user_id"],
        "username": data["message"]["from"].get("username", ""),
        "first_name": data["message"]["from"].get("first_name", ""),
        "last_name": data["message"]["from"].get("last_name", ""),
    }
    team = sm.app.current_teams.get(data["chat_id"], [])
    team.append(player_data)
    sm.app.current_teams[data["chat_id"]] = team
    #
    player, _ = await sm.accessor.get_or_create_player(player_data)
    await sm.accessor.add_player_to_current_team(data["chat_id"], player)


def condition_for_quasi_callback(sm: "StateMachine", data: dict):
    reply = data["message"].get("reply_to_message", False)
    owner = data["message"]["from"]["id"] == data["message"]["chat"]["id"]
    return reply or owner


# здесь просиходит подтверждение нажатия на кнопку запуска игры.. неоднозначный способ, но какой уж есть
async def await_coplayers(sm: "StateMachine", data: dict):
    if condition_for_quasi_callback(sm, data):
        if data["message"]["text"] == "Запустить игру!":
            sm.app.user_states[data["user_chat_id"]] = "ignore"
            return await launch_game(sm, data)
    else:
        return {}


async def _edit_reply_buttons(sm: "StateMachine", data: dict):
    edited_markup = data["message"]["reply_markup"]
    edited_markup["inline_keyboard"].insert(
        -1,
        [
            {
                "text": generate_random_emoji()
                + " @"
                + data["message"]["from"]["first_name"],
                "callback_data": "ignore",
            },
        ],
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
        msg = "Вы уже в команде!"
    else:
        await add_player_to_team(sm, data)
        msg = f"{data['message']['from'].get('first_name', 'Инкогнито..')} присоединяется к команде!"
        await _edit_reply_buttons(sm, data)
    return {"text": msg}


async def ignore(sm: "StateMachine", data: dict):
    return {}  # empty message


def current_game(sm: "StateMachine", data: dict):
    return sm.app.current_games.get(data["chat_id"], False)


def current_team(sm: "StateMachine", data: dict):
    return sm.app.current_teams.get(data["chat_id"], [])


def user_in_team(sm: "StateMachine", data: dict):
    return data["user_id"] in [p["user_id"] for p in current_team(sm, data)]


#
async def test_question(sm: "StateMachine", data: dict):
    ts = datetime.now()
    try:
        res = gpt_master.get_question(get_theme(), count=5)
    except APIConnectionError as exp:
        print("Oh no! API error!", exp)
        return {"text": f"Oh no! API error! {exp}"}
    duration = f"duration: {(datetime.now() - ts).total_seconds()}sec."

    for question in res:
        await sm.accessor.execute_query_creation(
            QuestionModel(
                question=question.question,
                answers=question.answers,
                story=question.story,
                context=question.context,
            )
        )
        await sm.app.sender.query(
            "sendMessage",
            {
                "text": dict_to_readable_text(question.__dict__),
                "chat_id": data["chat_id"],
            },
        )
    #
    return {"text": duration}


async def get_new_questions(sm: "StateMachine", data: dict):
    try:
        res = gpt_master.get_question(get_theme(), count=5)
    except APIConnectionError as exp:
        print("Oh no! API error!", exp)
        raise APIConnectionError

    questions = []
    for question in res:
        try:
            question_model = await sm.accessor.execute_query_creation(
                QuestionModel(
                    question=question.question,
                    answers=question.answers,
                    story=question.story,
                    context=question.context,
                )
            )
            questions.append(question_model)
        except DBAPIError as exp:
            print("Error on sqlAlchemy:", exp)
            continue
    #
    questions = [question.to_dataclass() for question in questions]
    #
    return questions

async def statistic(sm: "StateMachine", data: dict):
    game = await sm.accessor.get_last_game()
    game = game.to_serializable()
    # game = game.to_serializable()
    # stat = [
    #     f"Статистика по последней игре от {game['created_at'].split('.')[0]}",
    #     f"Счет игры: "
    # ]
    # return {'text': '\n\n'.join(stat)}
    return {'text': dict_to_readable_text(game)}


async def test(sm: "StateMachine", data: dict):
    asd = await add_player_to_team(sm, data)
    return {"text": f"{asd}"}
