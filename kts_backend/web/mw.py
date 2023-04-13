import typing

from aiohttp import web
from aiohttp.abc import Request
from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec.middlewares import validation_middleware
from aiohttp_session import get_session

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


@web.middleware
async def example_mw(request: Request, handler):
    #
    return await handler(request)


@web.middleware
async def auth_middleware(request: Request, handler):
    session = await get_session(request)
    if session:
        request.admin = session.get('admin')
    #
    return await handler(request)


@web.middleware
async def api_errors_handler_middleware(request: Request, handler):
    response = await handler(request)
    return response


@web.middleware
async def login_required(request: Request, handler):
    from kts_backend.api.views import (
        GetLastGame, GetPlayers, GetQuestions, MakeQuestions
    )
    if handler in [GetLastGame, GetPlayers, GetQuestions, MakeQuestions]:
        session = await get_session(request)
        if not session.get('admin', False):
            raise HTTPForbidden
    #
    response = await handler(request)
    return response


def setup_middlewares(app: "Application"):
    app.middlewares.append(auth_middleware)
    app.middlewares.append(validation_middleware)
    app.middlewares.append(api_errors_handler_middleware)
    app.middlewares.append(login_required)
