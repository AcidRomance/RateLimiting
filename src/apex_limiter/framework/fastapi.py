from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.config import get_settings, Settings
from apex_limiter.core.limiter import RateLimiter
from apex_limiter.core.rules import RateLimitRule
from apex_limiter.storage.base import IStorage
from apex_limiter.storage.redis import RedisStorage


@lru_cache(maxsize=1)
def get_redis_client() -> Redis[bytes]:
    """DI: Создает и кэширует синглтон-клиент Redis."""
    settings = get_settings()
    return Redis.from_url(settings.REDIS_URL.get_secret_value(), decode_responses=False)


@lru_cache(maxsize=1)
def get_limiter_storage(
    redis_client: Annotated[Redis[bytes], Depends(get_redis_client)],
) -> IStorage:
    """DI: Создает и кэширует синглтон-хранилище."""
    return RedisStorage(client=redis_client)


def rate_limiter_dependency(
    rules: list[RateLimitRule],
) -> RateLimiter:
    """
    Фабрика зависимостей FastAPI.
    Создает экземпляр RateLimiter с заданными правилами.
    Это позволяет нам определять разные лимиты для разных эндпоинтов.
    """
    
    def _get_limiter(
        request: Request,
        storage: Annotated[IStorage, Depends(get_limiter_storage)],
    ) -> RateLimiter:
        return RateLimiter(storage=storage, rules=rules)

    return Depends(_get_limiter)


async def rate_limit_checker(
    request: Request,
    limiter: Annotated[RateLimiter, Depends(rate_limiter_dependency)],
):
    """
    Общая зависимость для проверки лимитов.
    Использует IP-адрес клиента как идентификатор.
    Если лимит превышен, выбрасывает HTTPException 429.
    """
    # В реальном приложении идентификатором может быть API-ключ или ID пользователя.
    identifier = request.client.host if request.client else "unknown"
    if not await limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests",
        )