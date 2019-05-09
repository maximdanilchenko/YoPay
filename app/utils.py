import decimal

import simplejson
from aiohttp import web


def json_response(data: dict, *, status: int = 200, error: str = None) -> web.Response:
    if error:
        data["error"] = error
    # Use simplejson to support Decimal rendering as JSON
    return web.json_response(data, status=status, dumps=simplejson.dumps)


def convert_amount(
    *,
    rate_from: decimal.Decimal = decimal.Decimal("1.00"),
    rate_to: decimal.Decimal = decimal.Decimal("1.00"),
    amount: decimal.Decimal
) -> decimal.Decimal:
    if rate_from == rate_to:
        return amount
    places = decimal.Decimal((0, (1,), -2))
    quotation = rate_to / rate_from
    amount = amount * quotation
    return amount.quantize(places)