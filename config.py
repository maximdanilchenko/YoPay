from os import environ

config = {
    "POSTGRES": {
        "DSN": environ["POSTGRES_DSN"],
        "POOL_MIN_SIZE": int(environ["POSTGRES_POOL_MIN_SIZE"]),
        "POOL_MAX_SIZE": int(environ["POSTGRES_POOL_MAX_SIZE"]),
    },
    "REDIS": {
        "DSN": environ["REDIS_DSN"],
        "POOL_MIN_SIZE": int(environ["REDIS_POOL_MIN_SIZE"]),
        "POOL_MAX_SIZE": int(environ["REDIS_POOL_MAX_SIZE"]),
    },
    "SESSION_EXPIRES": 86_400,
    "RATES": {"UPDATE_INTERVAL": 60, "URL": "https://api.exchangeratesapi.io/latest"},
    "STATUS_MANAGER_TOKEN": environ["STATUS_MANAGER_TOKEN"],
    "PRIVATE_KEY": "test_private_key.pem",
}
