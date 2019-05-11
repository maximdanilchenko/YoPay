import uuid

import sqlalchemy as sa
from aiohttp import web
from aiohttp_apispec import docs, request_schema
from aioredis.commands import Redis
from databases import Database
from passlib.hash import pbkdf2_sha256

from app.db.postgres.models import users, wallets
from app.schemas import Registration, User
from app.utils import json_response


@docs(tags=["auth"], summary="User registration")
@request_schema(Registration)
async def signup(request: web.Request):
    db: Database = request.app["db"]
    user = request["data"]["user"]
    wallet_currency = request["data"]["wallet_currency"]

    async with db.connection() as con:
        # Checking login uniqueness
        login_exists = await con.fetch_val(
            sa.select([sa.exists(users.select().where(users.c.login == user["login"]))])
        )
        if login_exists:
            return json_response({"user": {"login": "Already exists."}}, status=422)

        user["password"] = pbkdf2_sha256.hash(user["password"])

        # Use transaction to make sure both user and wallet are created
        async with con.transaction():
            # Creating user
            user_id = await con.fetch_val(
                users.insert().values(user).returning(users.c.id)
            )
            # Creating user wallet
            await con.execute(
                wallets.insert().values(
                    user_id=user_id, amount=0, currency=wallet_currency
                )
            )
            return json_response({})


@docs(tags=["auth"], summary="User authorization")
@request_schema(User(only=["login", "password"]))
async def login(request: web.Request):
    db: Database = request.app["db"]
    redis: Redis = request.app["redis"]
    user = request["data"]

    actual_user = await db.fetch_one(
        sa.select([users.c.id, users.c.password]).where(users.c.login == user["login"])
    )

    # Login not found
    if not actual_user:
        return json_response({}, status=401)

    # Password is incorrect
    if not pbkdf2_sha256.verify(user["password"], actual_user["password"]):
        return json_response({}, status=401)

    session_token = str(uuid.uuid4())
    await redis.setex(
        key=session_token,
        value=actual_user["id"],
        seconds=request.app["config"]["SESSION_EXPIRES"],
    )

    return json_response({"token": session_token})
