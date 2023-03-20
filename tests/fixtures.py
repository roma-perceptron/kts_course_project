import pytest
from kts_backend.web.app import setup_app


@pytest.fixture(scope="session")
async def app():
    app = await setup_app()
    return app
