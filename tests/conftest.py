import factory
import pytest
import sqlalchemy as sa
from passlib.hash import pbkdf2_sha256

from app import create_app
from app.constants import WalletCurrencies
from app.db.postgres.models import users, wallets
from config import config


class User1(factory.DictFactory):
    name = "John"
    country = "Westeros"
    city = "Winterfell"
    login = "john123"
    password = "iknownothing"


class User1Insert(User1):
    password = pbkdf2_sha256.hash(User1.password)


class User2(User1):
    login = "johnclone"


class User2Insert(User2):
    password = pbkdf2_sha256.hash(User2.password)


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


@pytest.fixture(autouse=True)
def mock_rates():
    pass


@pytest.fixture
async def create_users(cli):
    db = cli.app["db"]
    async with db.transaction(force_rollback=True):
        for user in (User1Insert(), User2Insert()):

            user_id = await db.fetch_val(
                users.insert().values(user).returning(users.c.id)
            )
            await db.execute(
                wallets.insert().values(
                    user_id=user_id, amount=0, currency=WalletCurrencies.USD
                )
            )
        yield


@pytest.fixture
async def user_selector(cli):
    db = cli.app["db"]

    async def selector(user):
        return await db.fetch_one(users.select(users.c.login == user["login"]))

    return selector


@pytest.fixture
async def wallet_selector(cli):
    db = cli.app["db"]

    async def selector(user):
        return await db.fetch_one(
            sa.select([wallets.c.amount, wallets.c.currency])
            .select_from(wallets.join(users))
            .where(users.c.login == user["login"])
        )

    return selector


@pytest.fixture
async def user_authorizer(cli):
    async def authorizer(user):
        resp = await cli.post(
            "/api/auth/login",
            json={"password": user["password"], "login": user["login"]},
        )
        return {"Authorization": (await resp.json())["token"]}

    return authorizer
