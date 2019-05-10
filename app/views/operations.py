import datetime as dt

import sqlalchemy as sa
from aiohttp import web
from aiohttp_apispec import docs, request_schema
from databases import Database

from app.constants import ALLOWED_TRANSACTIONS, OperationStatuses
from app.db.postgres.models import operations, operations_statuses, wallets
from app.decorators import authorized_status_manager
from app.schemas import OperationStatus
from app.utils import convert_amount, json_response


@docs(
    tags=["operations"],
    security={"status-manager": []},
    summary="Change operation status",
)
@authorized_status_manager
@request_schema(OperationStatus)
async def change_status(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    operation_id = int(request.match_info["operation_id"])
    new_status = request["data"]["status"]

    async with db.connection() as con:

        operation = await con.fetch_one(
            sa.select([*operations.c, operations_statuses.c.status])
            .select_from(operations.join(operations_statuses))
            .where(operations.c.id == operation_id)
            .order_by(sa.desc(operations_statuses.c.id))
            .limit(1)
        )

        if not operation:
            return json_response({}, status=404, error="Operation not found")

        if new_status not in ALLOWED_TRANSACTIONS[operation["status"]]:
            return json_response({}, status=400, error="Not valid status")
        async with con.transaction():
            if (
                operation["status"] == OperationStatuses.DRAFT
                and new_status == OperationStatuses.PROCESSING
            ):
                sender_wallet = await con.fetch_one(
                    wallets.select().where(
                        wallets.c.id == operation["sender_wallet_id"]
                    )
                )
                amount_from_sender = convert_amount(
                    rate_to=operation["sender_wallet_rate"], amount=operation["amount"]
                )
                if sender_wallet["amount"] < amount_from_sender:
                    return json_response(
                        {}, status=202, error="Not enough money on sender wallet"
                    )
                new_sender_amount = sender_wallet["amount"] - amount_from_sender
                await con.execute(
                    sa.update(wallets)
                    .values(amount=new_sender_amount)
                    .where(wallets.c.id == operation["sender_wallet_id"])
                )

            elif operation["status"] == OperationStatuses.PROCESSING:
                if new_status == OperationStatuses.ACCEPTED:
                    amount_to_receiver = convert_amount(
                        rate_to=operation["receiver_wallet_rate"],
                        amount=operation["amount"],
                    )
                    await con.execute(
                        sa.update(wallets)
                        .values(amount=wallets.c.amount + amount_to_receiver)
                        .where(wallets.c.id == operation["receiver_wallet_id"])
                    )
                elif new_status == OperationStatuses.FAILED:
                    amount_to_sender = convert_amount(
                        rate_to=operation["sender_wallet_rate"],
                        amount=operation["amount"],
                    )
                    await con.execute(
                        sa.update(wallets)
                        .values(amount=wallets.c.amount + amount_to_sender)
                        .where(wallets.c.id == operation["sender_wallet_id"])
                    )
            await con.execute(
                operations_statuses.insert().values(
                    operation_id=operation_id,
                    status=new_status,
                    datetime=dt.datetime.utcnow(),
                )
            )

    operation = dict(operation)
    operation["status"] = new_status
    operation["datetime"] = operation["datetime"].isoformat()

    return json_response(operation)
