import os
import typing

import jinja2
import aiohttp_jinja2
from aiohttp import web

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


def setup_routes(app: "Application"):
    from kts_backend.api.views import (
        IndexView,
        LoginView,
        TestView, GetLastGame, GetPlayers, GetQuestions, MakeQuestions
    )
    #
    # print('here:', os.getcwd())
    # print('is exist kts_backend/static:', os.path.exists('kts_backend/static'))
    # print(os.listdir('kts_backend/static'))
    if os.path.exists('kts_backend/static'):
        print('*'*55, "NORMAL")
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('kts_backend/templates'))
        app.add_routes([web.static('/app_static', 'kts_backend/static')])
    else:
        print('*'*55, "VPS")
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('/home/kts_template_project/kts_backend/templates'))
        app.add_routes([web.static('/app_static', '/home/kts_template_project/kts_backend/static')])
    app.router.add_view("/", IndexView)
    #

    app.router.add_view("/login", LoginView)
    #
    app.router.add_view("/test", TestView)
    app.router.add_view("/get_last_game", GetLastGame)
    app.router.add_view("/get_players", GetPlayers)
    app.router.add_view("/get_questions", GetQuestions)
    app.router.add_view("/make_questions", MakeQuestions)

