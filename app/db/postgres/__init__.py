from aiohttp import web
from databases import Database


async def init_postgres(app: web.Application):
    app["db"] = Database(
        app["config"]["POSTGRES"]["DSN"],
        min_size=app["config"]["POSTGRES"]["POOL_MIN_SIZE"],
        max_size=app["config"]["POSTGRES"]["POOL_MAX_SIZE"],
    )
    await app["db"].connect()


async def close_postgres(app: web.Application):
    await app["db"].disconnect()
