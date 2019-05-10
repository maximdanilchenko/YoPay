from functools import wraps

from aiohttp import web
from aioredis.commands import Redis


def authorized_user(*args, **kwargs):
    """
    Auth decorator. It could be callable or not - it
    made for optional "allow_unauthorized" parameter
    """

    if args and callable(args[0]):
        view_func = args[0]
    else:
        view_func = None

    allow_unauthorized = kwargs.get("allow_unauthorized", False)

    def authorized(func):
        @wraps(func)
        async def wrapper(request: web.Request):
            redis: Redis = request.app["redis"]
            unauthorized = False

            # Checking auth header
            try:
                auth_header = request.headers["Authorization"]
            except KeyError:
                unauthorized = True
            else:
                # Founding user session
                user_id = await redis.get(key=auth_header)
                if not user_id:
                    unauthorized = True
                request["user_id"] = int(user_id)

            if unauthorized and not allow_unauthorized:
                return web.json_response({}, status=401)

            return await func(request)

        return wrapper

    return authorized(view_func) if view_func else authorized


def authorized_status_manager(func):
    """
    Checking for "X-Status-Manager-Token" header for status management system auth
    """

    @wraps(func)
    async def wrapper(request: web.Request):

        # Checking auth header
        try:
            auth_header = request.headers["X-Status-Manager-Token"]
        except KeyError:
            return web.json_response({}, status=401)

        if auth_header != request.app["config"]["STATUS_MANAGER_TOKEN"]:
            return web.json_response({}, status=401)

        return await func(request)

    return wrapper
