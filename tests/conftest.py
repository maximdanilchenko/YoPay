import pytest

from app import create_app
from config import config


@pytest.fixture
def cli(loop, aiohttp_client):
    app = create_app(config)
    return loop.run_until_complete(aiohttp_client(app))
