import decimal

import simplejson
from aiohttp import ClientResponse, ClientSession, web
from aioredis.commands import Redis

from app.constants import WalletCurrencies

RATES_KEY = "rates"


class RatesClient:
    def __init__(self):
        self.session = None
        self.url = None
        self.params = {
            "base": WalletCurrencies.USD.value,
            "symbols": ",".join(
                [
                    WalletCurrencies.USD.value,
                    WalletCurrencies.EUR.value,
                    WalletCurrencies.CAD.value,
                    WalletCurrencies.CNY.value,
                ]
            ),
        }
        self.update_interval = None
        self.app = None

    async def on_startup(self, app: web.Application):
        self.app = app
        self.url = app["config"]["RATES"]["URL"]
        self.update_interval = app["config"]["RATES"]["UPDATE_INTERVAL"]
        self.session = ClientSession()
        app["rates_client"] = self

    async def on_cleanup(self, app: web.Application):
        await self.session.close()

    @classmethod
    def register_app(cls, app: web.Application):
        instance = cls()
        app.on_startup.append(instance.on_startup)
        app.on_cleanup.append(instance.on_cleanup)

    async def get_rates(self):
        redis: Redis = self.app["redis"]

        rates = await redis.get(RATES_KEY)
        if rates:
            rates = simplejson.loads(rates)
        else:
            response: ClientResponse = await self.session.get(
                self.url, params=self.params
            )
            data = await response.json()
            rates = data["rates"]

            await redis.setex(
                key=RATES_KEY,
                value=simplejson.dumps(rates),
                seconds=self.update_interval,
            )

        return {WalletCurrencies(k): decimal.Decimal(str(v)) for k, v in rates.items()}
