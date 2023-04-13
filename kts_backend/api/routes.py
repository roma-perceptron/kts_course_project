import typing

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


def setup_routes(app: "Application"):
    from kts_backend.api.views import (
        LoginView,
        TestView, GetLastGame, GetPlayers, GetQuestions, MakeQuestions
    )

    app.router.add_view("/login", LoginView)
    #
    app.router.add_view("/test", TestView)
    app.router.add_view("/get_last_game", GetLastGame)
    app.router.add_view("/get_players", GetPlayers)
    app.router.add_view("/get_questions", GetQuestions)
    app.router.add_view("/make_questions", MakeQuestions)

