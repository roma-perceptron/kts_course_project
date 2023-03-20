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


class TestBot:
    async def test_dummy(self):
        # assert ЗНАЧЕНИЕ_ИЗ_КОДА == ИСТИНННОЕ_ОЖИДАЕМОЕ_ЗНАЧЕНИЕ
        assert 2 * 2 == 4
