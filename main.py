# import uvloop
from aiohttp import web

from app import create_app
from config import config

# uvloop.install()


app = create_app(config)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8765)
