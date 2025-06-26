import pytest_asyncio
from fakeredis.aioredis import FakeRedis

from apex_limiter.storage.redis import RedisStorage


@pytest_asyncio.fixture
async def fake_redis() -> FakeRedis:
    """Фикстура, предоставляющая 'фейковый' Redis клиент для тестов."""
    client = FakeRedis()
    yield client
    await client.flushall()
    await client.close()


@pytest_asyncio.fixture
async def redis_storage(fake_redis: FakeRedis) -> RedisStorage:
    """Фикстура, предоставляющая хранилище на базе 'фейкового' Redis."""
    return RedisStorage(client=fake_redis)