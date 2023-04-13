import typing

import pytest
from kts_backend.web.app import setup_app

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


@pytest.fixture(scope="session")
async def app():
    app = await setup_app(config_path='config.yml')
    app.test_field = "Yeah!"
    return app
