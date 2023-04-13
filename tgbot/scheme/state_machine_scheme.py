from tgbot.state_machine_functions import (
    start_team, await_coplayers, join_team, ignore, await_launch,
    await_choose_player_who_answer, await_answer, stop_game, ready_for_early_answer, statistic,
    get_new_questions, help
)

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
    {
        'command': '/help',
        'description': 'Подробное описание',
        'action': help
    },
    {
        'command': '/statistic',
        'description': 'Посмотреть статистику',
        'action': statistic
    },
    {
        'command': '/new_questions',
        'description': 'Сгенерировать несколько случайных вопросов',
        'action': get_new_questions
    },
    # --- --- --- --- --- --- --- --- --- --- --- --- КОМАНДЫ --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    #
    # --- --- --- --- --- --- --- --- --- --- --- -- СОСТОЯНИЯ --- --- --- --- --- --- --- --- --- --- --- --- --- --
    {
        'command': 'await_coplayers',
        'description': '',
        'action': await_coplayers
    },
    {
        'command': 'await_launch',
        'description': '',
        'action': await_launch
    },
    {
        'command': 'await_choose_player_who_answer',
        'description': '',
        'action': await_choose_player_who_answer
    },
    {
        'command': 'await_answer',
        'description': '',
        'action': await_answer
    },
    {
        'command': 'ready_for_early_answer',
        'description': '',
        'action': ready_for_early_answer
    },
    # --- --- --- --- --- --- --- --- --- --- --- -- СОСТОЯНИЯ --- --- --- --- --- --- --- --- --- --- --- --- --- --
    #
    # --- --- --- --- --- --- --- --- --- --- --- --  КОЛБЕКИ  -- --- --- --- --- --- --- --- --- --- --- --- --- ---
    {
        'command': '',
        'description': 'Присоединиться к команде',
        'action': ignore
    },
    {
        'command': 'ignore',
        'description': 'Присоединиться к команде',
        'action': ignore
    },
    {
        'command': 'join_team',
        'description': 'Присоединиться к команде',
        'action': join_team
    },
    # --- --- --- --- --- --- --- --- --- --- --- --  КОЛБЕКИ  -- --- --- --- --- --- --- --- --- --- --- --- --- ---
]