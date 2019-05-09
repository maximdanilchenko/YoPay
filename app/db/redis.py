import aioredis
from aiohttp import web


async def init_redis(app: web.Application):
    app["redis"] = await aioredis.create_redis_pool(
        app["config"]["REDIS"]["DSN"],
        minsize=app["config"]["REDIS"]["POOL_MIN_SIZE"],
        maxsize=app["config"]["REDIS"]["POOL_MAX_SIZE"],
    )


async def close_redis(app: web.Application):
    app["redis"].close()
    await app["redis"].wait_closed()
