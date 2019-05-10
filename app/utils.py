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
    """ Convert amount of money from one currency to another based on its rates. """
    if rate_from == rate_to:
        return amount
    quotation = rate_to / rate_from
    amount = amount * quotation
    return amount.quantize(decimal.Decimal(".01"))
