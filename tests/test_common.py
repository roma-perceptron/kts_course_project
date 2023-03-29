import typing

import pytest

# class TestCommon:
#     async def test_404(self, cli):
#         response = await cli.get("/")
#         assert response.status == 404
#         assert await response.json() == {
#             "status": "error",
#             "data": {},
#             "code": None,
#             "message": "404: Not Found",
#         }
#
# if typing.TYPE_CHECKING:
#     from kts_backend.web.app import Application


class TestBot:
    def test_dummy(self):
        # assert ЗНАЧЕНИЕ_ИЗ_КОДА == ИСТИНННОЕ_ОЖИДАЕМОЕ_ЗНАЧЕНИЕ
        assert 2 * 2 == 4


class TestApp:
    async def test_app(self, app):
        app = await app
        assert app.test_field == "Yeah!"
