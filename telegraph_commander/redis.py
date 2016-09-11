import asyncio_redis

redis_client = None

async def get_redis_client(config):
    global redis_client
    if redis_client is not None:
        return redis_client

    redis_client = await asyncio_redis.Connection.create(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT
    )
    return redis_client
