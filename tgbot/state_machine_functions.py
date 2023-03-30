import asyncio
import json
import random
import typing
import uuid

from datetime import datetime, timedelta

from kts_backend.utils import dict_to_readable_text, generate_random_emoji
from chatgpt import Question, FAKE_QUESTION

if typing.TYPE_CHECKING:
    from tgbot.tgbot import StateMachine

NUMBER_ROUNDS = 3
WIN_SCORE = NUMBER_ROUNDS // 2 + 1
TIME_TO_THINKING = 20
TIME_TO_ANSWER = 10
TIME_BETWEEN_ROUNDS = 5
POINTER = u'\U0001F449' + ' '

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


async def _send_launch_button(sm: "StateMachine", data: dict):
    reply_markup = {
        "keyboard": [[{"text": "Запустить игру!"}]],
        # "one_time_keyboard": True,
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
        'chat_id': data['chat_id'],
        'text': f"Начинаем {len(game['rounds']) + 1}-й раунд!"
    }
    await sm.app.sender.query('sendMessage', kwargs_for_reply)
    return game


async def _send_question(sm, data, question: Question):
    # сначала закидываем историю
    kwargs_for_reply = {
        'chat_id': data['chat_id'],
        'text': question.story
    }
    await sm.app.sender.query('sendMessage', kwargs_for_reply)
    await asyncio.sleep(1)  # 5sec

    # теперь сам вопрос
    kwargs_for_reply['text'] = f"Внимание вопрос:\n{question.question}"
    await sm.app.sender.query('sendMessage', kwargs_for_reply)
    await asyncio.sleep(1)  # 2



async def start_round(sm: "StateMachine", data: dict):
    await asyncio.sleep(1)

    # сообщение о раунде
    game = await _send_round_caption(sm, data)

    # формируем и задаем вопрос
    game_round = {
        'question': FAKE_QUESTION,
        'team_answer': '',
        'score': 0
    }
    game['rounds'].append(game_round)
    await _send_question(sm, data, game_round['question'])

    # добавляю в расписание таймер и начинается отсчет времени
    sm.app.timer_schedule.append(
        {
            'time': datetime.now() + timedelta(seconds=TIME_TO_THINKING),
            'chat_id': data['chat_id'],
            'command': continue_round,
            'executed': False,
            'type': 'continue_round',
        }
    )
    print('set timer, for [continue_round] -->', sm.app.timer_schedule[-1]['time'])
    #
    return {'text': 'У вас минута на обсуждение!'}


async def _checkout_score(game: dict):
    wisemans_score = sum(game_round['score'] for game_round in game['rounds'])
    chatgpts_score = len(game['rounds']) - wisemans_score
    #
    if wisemans_score > chatgpts_score:
        winners = 'Знатоки ведут!'
    elif chatgpts_score > wisemans_score:
        winners = 'ChatGPT ведет!'
    else:
        winners = 'Равный счет!'

    score = (wisemans_score, chatgpts_score)
    return f"Счет {wisemans_score}:{chatgpts_score}, {winners}", score


def _format_answer(answer: str):
    return answer.lower().strip()


async def _check_answer(sm: "StateMachine", data: dict, answer: str):
    game = current_game(sm, data)
    game_round = game['rounds'][-1]

    game_round['team_answer'] = answer
    f_answers = list(map(_format_answer, game_round['question'].answers))
    if answer.lower().strip() in f_answers:
        game_round['score'] = 1
        result = 'И это просто чудо, правильный ответ!'
    else:
        result = 'И это жуткая ересь!'
        result += '\n\nПравильный ответ: '
        result += ' или '.join(game_round['question'].answers)
    #
    score_str, score = await _checkout_score(game)
    #
    return result + '\n\n' + score_str, score


async def await_answer(sm: "StateMachine", data: dict):

    answer = data.get('message', {}).get('text', '')
    print(' '*6, 'await_answer', answer if answer else 'НЕ БЫЛО ОТВЕТА, ТАЙМАУТ')

    # надо выключить таймер, найдя его
    print(' '*6, 'timers:', sm.app.timer_schedule)
    for timer in sm.app.timer_schedule:
        if timer['chat_id'] == data['chat_id'] and timer['type'] == 'await_answer':
            timer['executed'] = True
            print(' '*6, 'kill timer', datetime.now(), timer['type'], timer['time'])

    # сначала повтор ответа
    kwargs_for_reply = {
        "chat_id": data["chat_id"],
        "text": f"Ваш ответ: {answer}" if answer else 'Вы не дали ответа в течении минуты',
        "reply_markup": json.dumps({"remove_keyboard": True}) if not answer else None
    }
    await sm.app.sender.query('sendMessage', kwargs_for_reply)

    # затираю состояния у всех юзеров текущей группы.. перезаписываю?
    print(' '*6, 'old states:', sm.app.user_states)
    sm.app.user_states = {
        user_chat_id: state for user_chat_id, state in sm.app.user_states.items()
        if user_chat_id.split(':')[1] != data['chat_id']
    }
    print('new states:', sm.app.user_states)

    # теперь собственно отработка ответа (даже если он пустой == неправильный)
    result, score = await _check_answer(sm, data, answer)
    if sum(score) == NUMBER_ROUNDS or score[0] == WIN_SCORE or score[1] == WIN_SCORE:
        result += '\n\nНа этом игра закончена, всем спасибо, все свободны!'
        # здесь еще надо сохранить все в БД..
        sm.app.current_games.pop(data['chat_id'])
        sm.app.current_teams.pop(data['chat_id'])
        sm.app.timer_schedule = [
            tt for tt in sm.app.timer_schedule
            if tt['chat_id'] != data['chat_id']
        ]
    else:
        # добавляю в расписание таймер для запуска следующего раунда
        sm.app.timer_schedule.append(
            {
                'time': datetime.now() + timedelta(seconds=TIME_BETWEEN_ROUNDS),
                'chat_id': data['chat_id'],
                'command': start_round,
                'executed': False,
                'type': 'start_round',
            }
        )
        print(' '*6, 'set timer for [start_round]', datetime.now(), ' -->', sm.app.timer_schedule[-1]['time'])
    kwargs_for_reply = {"text": result, 'chat_id': data['chat_id']}

    #
    return kwargs_for_reply



async def await_choose_player_who_answer(sm: "StateMachine", data: dict):
    if data["message"].get("reply_to_message", False):
        if data["message"]["text"].startswith(POINTER):
            player_who_answer = data["message"]["text"].replace(POINTER, '').strip()
            kwargs_for_reply = {
                "chat_id": data["chat_id"],
                "text": 'Капитан сделал свой выбор!',
                "reply_markup": json.dumps({"remove_keyboard": True}),
            }
            await sm.app.sender.query('sendMessage', kwargs_for_reply)

            #
            player_who_answer = [
                p for p in current_team(sm, data)
                if p['first_name'] == player_who_answer
            ][0]
            # ТУТ ЕСТЬ МЕСТО ДЛЯ КОСЯКА: username может вовсе отсутствовать у юзера телеги
            kwargs_for_reply = {
                "chat_id": data["chat_id"],
                "text": f"@{player_who_answer['username']} я весь во внимании:",
                "reply_markup": json.dumps({"force_reply": True, 'selective': True}),
            }
            uci = f"{player_who_answer['user_id']}:{data['chat_id']}"
            sm.app.user_states[uci] = "await_answer"
            #
            return kwargs_for_reply
    else:
        return {}


async def _choose_player_who_answer(sm: "StateMachine", data: dict):
    print(' '*3, '_choose_player_who_answer')
    players = current_team(sm, data)
    if not players:
        return None

    captain = players[0]
    #
    reply_markup = {
        "keyboard": [
            [{'text': POINTER + player.get('first_name', '?!')}] for player in players
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
    print(' '*3, 'user_states:', sm.app.user_states)
    await sm.app.sender.query("sendMessage", kwargs_for_reply)

    # добавляю таймер для ответа
    sm.app.timer_schedule.append(
        {
            'time': datetime.now() + timedelta(seconds=TIME_TO_ANSWER),
            'chat_id': data['chat_id'],
            'command': await_answer,
            'executed': False,
            'type': 'await_answer',
        }
    )
    print(' '*3, 'set timer for [await_answer] -->', sm.app.timer_schedule[-1]['time'])


async def continue_round(sm: "StateMachine", data: dict):
    print('continue_round')
    # сообщение об окончании времени на размышление
    await sm.app.sender.query(
        'sendMessage',
        {
            'text': 'Дамы и Господа, время вышло!', 'chat_id': data['chat_id']
        }
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
    await sm.app.sender.query('sendMessage', kwargs_for_reply)

    # назначение капитана: капитан это первый юзер в списке игроков команды
    team = current_team(sm, data)
    captain = random.choice(team)
    team.remove(captain)
    team.insert(0, captain)
    sm.app.current_teams[data['chat_id']] = team
    kwargs_for_reply = {
        'chat_id': data['chat_id'],
        'text': f"В этой игре капитаном будет {captain['first_name']}",
    }
    await sm.app.sender.query('sendMessage', kwargs_for_reply)


    sm.app.current_games[data['chat_id']] = {
        'team_id': uuid.uuid4(),
        'team_users': current_team(sm, data),
        'rounds': []
    }
    return await start_round(sm, data)


async def start_team(sm: "StateMachine", data: dict):
    # сразу формирую словарь с данными юзера
    player_data = {
        'user_id': data["user_id"],
        'username': data['message']['from']['username'],
        'first_name': data['message']['from']['first_name'],
    }
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
        sm.app.current_teams[data["chat_id"]] = [player_data]
        await _send_launch_button(sm, data)
    else:
        if user_in_team(sm, data):
            msg = "В уже в команде! Ждем еще участников и начинаем!"
        else:
            sm.app.current_teams[data["chat_id"]].append(player_data)
            msg = "В этом чате уже начали создавать команду, добавил Вас"
        kwargs_for_reply = {"text": msg}
    return kwargs_for_reply


# здесь просиходит подтверждение нажатия на кнопку запуска игры.. неоднозначный способ, но какой уж есть
async def await_coplayers(sm: "StateMachine", data: dict):
    if data["message"].get("reply_to_message", False):
        if data["message"]["text"] == "Запустить игру!":
            return await launch_game(sm, data)
    else:
        return {}


async def _edit_reply_buttons(sm: "StateMachine", data: dict):
    edited_markup = data["message"]["reply_markup"]
    edited_markup["inline_keyboard"].insert(-1, [
        {
            "text": generate_random_emoji()
            + " @"
            + data["message"]["from"]["first_name"],
            "callback_data": "ignore",
        },
    ])
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
        player_data = {
            'user_id': data["user_id"],
            'username': data['message']['from']['username'],
            'first_name': data['message']['from']['first_name'],
        }
        sm.app.current_teams[data["chat_id"]].append(player_data)
        msg = f"{data['message']['from'].get('first_name', 'Инкогнито..')} присоединяется к команде!"
        await _edit_reply_buttons(sm, data)
    return {"text": msg}


async def ignore(sm: "StateMachine", data: dict):
    return {}  # empty message


def current_game(sm: "StateMachine", data: dict):
    return sm.app.current_games.get(data['chat_id'], False)


def current_team(sm: "StateMachine", data: dict):
    return sm.app.current_teams.get(data["chat_id"], [])


def user_in_team(sm: "StateMachine", data: dict):
    return data["user_id"] in [p['user_id'] for p in current_team(sm, data)]
