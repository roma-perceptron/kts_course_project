from tgbot.state_machine_functions import (
    get_players, make_fake_game, get_last_game, example, start_team,
    await_coplayers, join_team, ignore, await_launch,
    await_choose_player_who_answer, await_answer, test_question, test, stop_game)

BOT_COMMANDS_AND_STATES = [
    # --- --- --- --- --- --- --- --- --- --- --- --- КОМАНДЫ --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    {
        'command': '/start',
        'description': 'Начать игру (начать собирать команду для игры)',
        'action': start_team
    },
    {
        'command': '/stop_game',
        'description': 'Остановить игру и распустить команду',
        'action': stop_game
    },
    # {
    #     'command': '/fake_game',
    #     'description': 'Создать новую демо-игру',
    #     'action': make_fake_game
    # },
    # {
    #     'command': '/get_game',
    #     'description': 'Получить данные последней игры',
    #     'action': get_last_game
    # },
    # {
    #     'command': '/get_players',
    #     'description': 'Показать всех игроков',
    #     'action': get_players
    # },
    # {
    #     'command': '/test',
    #     'description': 'Сгенерировать несколько случайных вопросов',
    #     'action': test
    # },
    # {
    #     'command': '/chatgpt',
    #     'description': 'Сгенерировать несколько случайных вопросов',
    #     'action': test_question
    # },
    # --- --- --- --- --- --- --- --- --- --- --- --- КОМАНДЫ --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    #
    # --- --- --- --- --- --- --- --- --- --- --- -- СОСТОЯНИЯ --- --- --- --- --- --- --- --- --- --- --- --- --- --
    # {
    #     'command': 'await_coplayers',
    #     'description': 'Ожидание остальных участников',
    #     'action': example
    # },
    {
        'command': 'await_coplayers',
        'description': 'test here',
        'action': await_coplayers
    },
    {
        'command': 'await_launch',
        'description': 'test here',
        'action': await_launch
    },
    {
        'command': 'await_choose_player_who_answer',
        'description': 'test here',
        'action': await_choose_player_who_answer
    },
    {
        'command': 'await_answer',
        'description': 'test here',
        'action': await_answer
    },
    # --- --- --- --- --- --- --- --- --- --- --- -- СОСТОЯНИЯ --- --- --- --- --- --- --- --- --- --- --- --- --- --
    #
    # --- --- --- --- --- --- --- --- --- --- --- --  КОЛБЕКИ  -- --- --- --- --- --- --- --- --- --- --- --- --- ---
    {
        'command': 'join_team',
        'description': 'Присоединиться к команде',
        'action': join_team
    },
    {
        'command': 'ignore',
        'description': 'Присоединиться к команде',
        'action': ignore
    },
    # --- --- --- --- --- --- --- --- --- --- --- --  КОЛБЕКИ  -- --- --- --- --- --- --- --- --- --- --- --- --- ---
    #
    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    {
        'command': 'test',
        'description': 'test here',
        'action': example
    },
]

# /start -> await_coplayers - in_game/captain_in_game
