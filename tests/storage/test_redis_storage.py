import asyncio
import time
from datetime import timedelta

import pytest

from apex_limiter.core.rules import RateLimitRule
from apex_limiter.storage.redis import RedisStorage


@pytest.mark.asyncio
async def test_redis_storage_allows_under_limit(redis_storage: RedisStorage):
    """
    Тест: Хранилище должно разрешать запросы, пока лимит не достигнут.
    """
    rule = RateLimitRule(limit=3, period=timedelta(seconds=10))
    identifier = "user-1"

    assert await redis_storage.check_and_update(rule, identifier) is True
    assert await redis_storage.check_and_update(rule, identifier) is True
    assert await redis_storage.check_and_update(rule, identifier) is True


@pytest.mark.asyncio
async def test_redis_storage_denies_over_limit(redis_storage: RedisStorage):
    """
    Тест: Хранилище должно отклонить запрос, как только лимит превышен.
    """
    rule = RateLimitRule(limit=2, period=timedelta(seconds=10))
    identifier = "user-2"

    # Первые 2 запроса должны пройти
    assert await redis_storage.check_and_update(rule, identifier) is True
    assert await redis_storage.check_and_update(rule, identifier) is True

    # Третий запрос должен быть отклонен
    assert await redis_storage.check_and_update(rule, identifier) is False


@pytest.mark.asyncio
async def test_redis_storage_window_slides_correctly(redis_storage: RedisStorage):
    """
    Тест: Проверка работы скользящего окна. Старые запросы должны "исчезать"
    из окна, позволяя делать новые.
    """
    rule = RateLimitRule(limit=1, period=timedelta(seconds=2))
    identifier = "user-3"

    # 1. Первый запрос проходит
    assert await redis_storage.check_and_update(rule, identifier) is True
    
    # 2. Второй запрос сразу же отклоняется
    assert await redis_storage.check_and_update(rule, identifier) is False
    
    # 3. Ждем, пока окно "проскользнет"
    await asyncio.sleep(2.1)
    
    # 4. Новый запрос должен быть разрешен, т.к. старый уже не в окне
    assert await redis_storage.check_and_update(rule, identifier) is True


@pytest.mark.asyncio
async def test_redis_storage_handles_different_identifiers_independently(
    redis_storage: RedisStorage
):
    """
    Тест: Лимиты для разных идентификаторов должны быть независимыми.
    """
    rule = RateLimitRule(limit=1, period=timedelta(seconds=10))
    identifier_a = "user-A"
    identifier_b = "user-B"

    # Оба могут сделать по одному запросу
    assert await redis_storage.check_and_update(rule, identifier_a) is True
    assert await redis_storage.check_and_update(rule, identifier_b) is True

    # Второй запрос для user-A отклоняется
    assert await redis_storage.check_and_update(rule, identifier_a) is False
    
    # Но для user-B все еще можно сделать новый запрос (если бы лимит был >1)
    # Здесь мы проверяем, что отказ для A не повлиял на B.
    # Чтобы доказать это, сделаем лимит 2
    rule_2 = RateLimitRule(limit=2, period=timedelta(seconds=10))
    assert await redis_storage.check_and_update(rule_2, identifier_b) is True
    assert await redis_storage.check_and_update(rule_2, identifier_b) is False