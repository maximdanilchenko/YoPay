import pytest

from passlib.hash import pbkdf2_sha256
import factory

from app import create_app
from config import config
from app.db.postgres.models import users, wallets
from app.constants import WalletCurrencies


class User1(factory.DictFactory):
    name = "Bob"
    country = "Westeros"
    city = "Winterfell"
    login = "bob123"
    password = "dragon2020"


class User1Insert(User1):
    password = pbkdf2_sha256.hash("dragon2020")


class User2(User1):
    login = "bobsson"


class User2Insert(User2):
    password = pbkdf2_sha256.hash("bobsson")


@pytest.fixture
def user1():
    return User1()


@pytest.fixture
def user2():
    return User2()


@pytest.fixture
def cli(loop, aiohttp_client):
    config["TESTING"] = True
    app = create_app(config)
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
async def create_users(cli):
    db = cli.app["db"]
    async with db.transaction(force_rollback=True):
        for user in (User1Insert(), User2Insert()):

            user_id = await db.fetch_val(
                users.insert()
                    .values(user)
                    .returning(users.c.id)
            )
            await db.execute(
                wallets.insert().values(
                    user_id=user_id, amount=0, currency=WalletCurrencies.USD
                )
            )
        yield


@pytest.fixture
async def select_user(cli):
    db = cli.app["db"]

    async def selector(login):
        return await db.fetch_one(
            users.select(users.c.login == login)
        )
    return selector
