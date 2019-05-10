import decimal
import datetime as dt
from freezegun import freeze_time

import pytest

from app.constants import WalletCurrencies


async def test_get_balance(cli, create_users, user1, wallet_selector, user_authorizer):
    resp = await cli.get("/api/wallet/balance", headers=await user_authorizer(user1))
    assert resp.status == 200
    assert await resp.json() == dict(await wallet_selector(user1))


@pytest.fixture(
    params=[
        ("100", WalletCurrencies.CNY),
        ("97.43", WalletCurrencies.USD),
        ("0.02", WalletCurrencies.CAD),
        ("111", WalletCurrencies.EUR),
    ]
)
def amount_currency(request):
    return request.param


async def test_post_balance(
    cli, create_users, user1, wallet_selector, user_authorizer, rates, amount_currency
):
    amount, currency = amount_currency
    resp = await cli.post(
        "/api/wallet/balance",
        headers=await user_authorizer(user1),
        json={"amount": amount, "currency": currency},
    )
    assert resp.status == 200
    wallet = await wallet_selector(user1)
    actual_amount = decimal.Decimal(amount) / rates[currency]
    assert wallet["amount"] == actual_amount.quantize(decimal.Decimal(".01"))


@freeze_time('2019-01-01T12:12:12.123')
async def test_create_operation(
    cli, create_users, user1, user2, user_authorizer, rates, amount_currency, wallet_selector, operation_selector
):
    amount, currency = amount_currency
    resp = await cli.post(
        "/api/wallet/operations",
        headers=await user_authorizer(user1),
        json={"amount": amount, "currency": currency, "receiver_login": user2["login"]},
    )
    assert resp.status == 200
    user1_wallet = await wallet_selector(user1)
    user2_wallet = await wallet_selector(user2)
    operation = await operation_selector(user1)
    assert operation["sender_wallet_rate"] == rates[user1_wallet["currency"]]
    assert operation["receiver_wallet_rate"] == rates[user2_wallet["currency"]]
    actual_amount = decimal.Decimal(amount) / rates[currency]
    assert operation["amount"] == actual_amount.quantize(decimal.Decimal(".01"))
    assert operation["datetime"] == dt.datetime(2019, 1, 1, 12, 12, 12, 123)
