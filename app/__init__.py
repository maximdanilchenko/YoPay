__version__ = "0.0.1"

from aiohttp import web
from aiohttp_apispec import setup_aiohttp_apispec, validation_middleware
from aiohttp_swagger import setup_swagger

from app.db.postgres import close_postgres, init_postgres
from app.db.redis import close_redis, init_redis
from app.rates_client import RatesClient
from app.routes import setup_routes


async def swagger(app: web.Application):
    setup_swagger(app=app, swagger_url="/api/doc", swagger_info=app["swagger_dict"])


def get_description() -> str:
    try:
        with open("description.md", "r") as description_file:
            description = description_file.read()
    except FileNotFoundError:
        description = ""
    return description


def create_app(config: dict) -> web.Application:
    app = web.Application()
    app["config"] = config

    setup_routes(app)

    setup_aiohttp_apispec(
        app,
        title="YoPay Pay System",
        version=__version__,
        info={"description": get_description()},
        securityDefinitions={
            "auth": {"type": "apiKey", "name": "Authorization", "in": "header"},
            "status-manager": {
                "type": "apiKey",
                "name": "X-Status-Manager-Token",
                "in": "header",
            },
        },
        tags=[
            {"name": "auth", "description": "Registration and authorization"},
            {"name": "wallet", "description": "Wallet management methods"},
            {"name": "reports", "description": "Reports generating"},
            {"name": "operations", "description": "Moving operations between statuses"},
        ],
    )

    app.on_startup.extend([swagger, init_postgres, init_redis])
    app.on_cleanup.extend([close_redis, close_postgres])

    app.middlewares.extend([validation_middleware])

    RatesClient.register_app(app)

    return app
