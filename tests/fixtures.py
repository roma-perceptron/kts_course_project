import typing

import pytest
from kts_backend.web.app import setup_app

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


@pytest.fixture(scope="session")
async def app():
    app = await setup_app()
    app.test_field = "Yeah!"
    return app
