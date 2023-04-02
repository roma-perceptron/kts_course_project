from tgbot.state_machine_functions import (
    example, start_team,
    await_coplayers, join_team, ignore, await_launch,
    await_choose_player_who_answer, await_answer, stop_game, ready_for_early_answer, statistic,
    test_question, test
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
        'command': '/statistic',
        'description': 'Посмотреть статистику',
        'action': statistic
    },
    # {
    #     'command': '/chatgpt',
    #     'description': 'Сгенерировать несколько случайных вопросов',
    #     'action': test_question
    # },
    # --- --- --- --- --- --- --- --- --- --- --- --- КОМАНДЫ --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    #
    # --- --- --- --- --- --- --- --- --- --- --- -- СОСТОЯНИЯ --- --- --- --- --- --- --- --- --- --- --- --- --- --
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
    {
        'command': 'ready_for_early_answer',
        'description': 'test here',
        'action': ready_for_early_answer
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