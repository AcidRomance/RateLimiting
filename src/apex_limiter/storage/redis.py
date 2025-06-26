import time
from typing import final

from redis.asyncio import Redis, StrictRedis

from apex_limiter.core.rules import RateLimitRule
from apex_limiter.storage.base import IStorage


@final
class RedisStorage(IStorage):
    """

    Реализация хранилища на базе Redis, использующая алгоритм
    Sliding Window Counter на основе Sorted Sets (ZSET).
    """

    def __init__(self, client: Redis[bytes]):
        self._redis = client

    async def check_and_update(
        self,
        rule: RateLimitRule,
        identifier: str,
    ) -> bool:
        """
        Выполняет атомарную проверку и обновление с помощью транзакции Redis (PIPELINE).

        1.  Определяет ключ в Redis для пары (правило, идентификатор).
        2.  Получает текущее время в виде float (UNIX timestamp).
        3.  В рамках одной транзакции:
            a.  Удаляет из ZSET все старые записи (старше `now - period`).
            b.  Добавляет новую запись с текущим временем и уникальным членом.
            c.  Получает количество оставшихся элементов в ZSET.
            d.  Устанавливает TTL для ключа, чтобы он автоматически удалился при неактивности.
        4.  Сравнивает результат (количество) с лимитом правила.
        """
        key = f"apex_limiter:{identifier}:{rule.get_unique_key()}"
        now = time.time()
        window_start = now - rule.period_seconds

        # Уникальный член для ZADD, чтобы избежать перезаписи при одинаковом score
        unique_member = f"{now}:{identifier}"

        # Используем pipeline для выполнения команд в одной транзакции
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {unique_member: now})
        pipe.zcard(key)
        # Устанавливаем TTL на ключ, равный периоду окна,
        # чтобы он автоматически очищался
        pipe.expire(key, rule.period_seconds)

        # Выполняем транзакцию и получаем результаты
        # result[0] - zremrangebyscore
        # result[1] - zadd
        # result[2] - zcard (это то, что нам нужно)
        # result[3] - expire
        results = await pipe.execute()

        current_count = results[2]
        return current_count <= rule.limit

    async def close(self) -> None:
        await self._redis.close()