import typing

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


def setup_routes(app: "Application"):
    from kts_backend.api.views import TestView, GetLastGame

    app.router.add_view("/test", TestView)
    app.router.add_view("/get_last_game", GetLastGame)

