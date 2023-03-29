from aiohttp.web import run_app
from kts_backend.web.app import setup_app


if __name__ == "__main__":
    # from random import choice
    # from chatgpt import chatgpt, themes
    # #
    # example = choice(themes.THEMES)
    # quest_maker = chatgpt.MasterOfTheGame()
    # proto_quest = chatgpt.Question(answers=[example.concept], context=example.context)
    # res = quest_maker.get_question(proto_quest, sys_context="Ты выражаешь мысли с помощью иносказаний и метафор")
    # #
    # # print(res)
    # #
    # for part in ['story', 'question', 'answers', 'context']:
    #     print(part, ': ', res.__dict__[part])
    # #
    # import json
    # print(f"[{json.dumps('start_meeting')}]")

    run_app(
        setup_app()
    )