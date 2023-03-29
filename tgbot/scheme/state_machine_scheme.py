from tgbot.state_machine_functions import (get_players, make_fake_game, get_last_game, example, start_team,
                                           await_coplayers, join_team, ignore, await_launch)

BOT_COMMANDS_AND_STATES = [
    # --- --- --- --- --- --- --- --- --- --- --- --- КОМАНДЫ --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    {
        'command': '/start',
        'description': 'Начать игру (начать собирать команду для игры)',
        'action': start_team
    },
    {
        'command': '/fake_game',
        'description': 'Создать новую демо-игру',
        'action': make_fake_game
    },
    {
        'command': '/get_game',
        'description': 'Получить данные последней игры',
        'action': get_last_game
    },
    {
        'command': '/get_players',
        'description': 'Показать всех игроков',
        'action': get_players
    },
    # --- --- --- --- --- --- --- --- --- --- --- --- КОМАНДЫ --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    #
    # --- --- --- --- --- --- --- --- --- --- --- -- СОСТОЯНИЯ --- --- --- --- --- --- --- --- --- --- --- --- --- --
    {
        'command': 'await_coplayers',
        'description': 'Ожидание остальных участников',
        'action': example
    },
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
