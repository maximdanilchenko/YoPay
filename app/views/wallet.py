import datetime as dt
from base64 import b64encode

import sqlalchemy as sa
from aiohttp import web
from aiohttp_apispec import docs, request_schema
from Crypto.Hash import SHA256
from databases import Database

from app.constants import OperationStatuses
from app.db.postgres.models import operations, operations_statuses, users, wallets
from app.decorators import authorized_user
from app.schemas import Money, MoneyReceiverLogin
from app.utils import convert_amount, json_response


@docs(tags=["wallet"], security={"auth": []}, summary="Get wallet balance info")
@authorized_user
async def get_balance(request: web.Request) -> web.Response:
    db: Database = request.app["db"]

    wallet = await db.fetch_one(
        sa.select([wallets.c.amount, wallets.c.currency]).where(
            wallets.c.user_id == request["user_id"]
        )
    )

    return json_response(dict(wallet))


@docs(tags=["wallet"], security={"auth": []}, summary="Put money on wallet balance")
@authorized_user
@request_schema(Money)
async def put_money_on_balance(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    money = request["data"]
    rates = await request.app["rates_client"].get_rates()

    async with db.connection() as con:
        wallet = await con.fetch_one(
            sa.select([wallets.c.amount, wallets.c.currency]).where(
                wallets.c.user_id == request["user_id"]
            )
        )

        new_amount = wallet["amount"] + convert_amount(
            rate_from=rates[money["currency"]],
            rate_to=rates[wallet["currency"]],
            amount=money["amount"],
        )

        await con.execute(
            wallets.update()
            .values(amount=new_amount)
            .where(wallets.c.user_id == request["user_id"])
        )

    return json_response({"amount": new_amount, "currency": wallet["currency"]})


@docs(tags=["wallet"], security={"auth": []}, summary="Send money to user")
@authorized_user
@request_schema(MoneyReceiverLogin)
async def create_operation(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    data = request["data"]
    rates = await request.app["rates_client"].get_rates()
    now_datetime = dt.datetime.utcnow()

    async with db.connection() as con:
        receiver_wallet = await con.fetch_one(
            sa.select([wallets.c.id, wallets.c.currency, users.c.id.label("user_id")])
            .select_from(wallets.join(users))
            .where(users.c.login == data["receiver_login"])
        )

        if not receiver_wallet:
            return json_response({}, status=404, error="Receiver not found")

        if receiver_wallet["user_id"] == request["user_id"]:
            return json_response({}, status=400, error="Should be another wallet")

        sender_wallet = await con.fetch_one(
            sa.select([wallets.c.id, wallets.c.currency, wallets.c.amount]).where(
                wallets.c.user_id == request["user_id"]
            )
        )

        signature = operation_signature(
            request.app["operations_signer"],
            sender_wallet["id"],
            receiver_wallet["id"],
            data["currency"],
            data["amount"],
            now_datetime,
        )

        async with con.transaction():
            operation_id = await con.fetch_val(
                operations.insert()
                .values(
                    sender_wallet_id=sender_wallet["id"],
                    receiver_wallet_id=receiver_wallet["id"],
                    amount=convert_amount(
                        rate_from=rates[data["currency"]], amount=data["amount"]
                    ),
                    sender_wallet_rate=rates[sender_wallet["currency"]],
                    receiver_wallet_rate=rates[receiver_wallet["currency"]],
                    datetime=now_datetime,
                    signature=signature,
                )
                .returning(operations.c.id)
            )
            await con.execute(
                operations_statuses.insert().values(
                    operation_id=operation_id,
                    status=OperationStatuses.DRAFT,
                    datetime=now_datetime,
                )
            )

    return json_response(
        {
            "id": operation_id,
            "amount": data["amount"],
            "currency": data["currency"],
            "datetime": now_datetime.isoformat(),
            "receiver_login": data["receiver_login"],
            "status": OperationStatuses.DRAFT,
            "signature": signature,
            "rates": rates,
        }
    )


def operation_signature(
    signer, sender_wallet_id, receiver_wallet_id, currency, amount, datetime
):
    """ Create sign for operation and return it in base64 decoded """
    data = f"{sender_wallet_id}{receiver_wallet_id}{currency}{amount}{datetime}"
    digest = SHA256.new()
    digest.update(data.encode())
    return b64encode(signer.sign(digest)).decode()
