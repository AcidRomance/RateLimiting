import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from apex_limiter.core.limiter import RateLimiter
from apex_limiter.core.rules import RateLimitRule
from apex_limiter.storage.base import IStorage

@pytest.fixture
def mock_storage() -> IStorage:
    """Фикстура для мока хранилища."""
    return AsyncMock(spec=IStorage)


@pytest.mark.asyncio
async def test_limiter_allows_if_storage_allows(mock_storage: IStorage):
    """
    Тест: RateLimiter должен разрешить запрос, если хранилище его разрешает.
    """
    mock_storage.check_and_update.return_value = True
    rule = RateLimitRule(limit=5, period=timedelta(seconds=10))
    limiter = RateLimiter(storage=mock_storage, rules=[rule])

    is_allowed = await limiter.is_allowed("test-id")

    assert is_allowed is True
    mock_storage.check_and_update.assert_called_once_with(rule, "test-id")


@pytest.mark.asyncio
async def test_limiter_denies_if_storage_denies(mock_storage: IStorage):
    """
    Тест: RateLimiter должен отклонить запрос, если хранилище его отклоняет.
    """
    mock_storage.check_and_update.return_value = False
    rule = RateLimitRule(limit=5, period=timedelta(seconds=10))
    limiter = RateLimiter(storage=mock_storage, rules=[rule])

    is_allowed = await limiter.is_allowed("test-id")

    assert is_allowed is False
    mock_storage.check_and_update.assert_called_once_with(rule, "test-id")


@pytest.mark.asyncio
async def test_limiter_checks_strictest_rule_first(mock_storage: IStorage):
    """
    Тест: RateLimiter должен проверять правила в порядке от самого строгого к самому мягкому.
    Если самое строгое правило нарушено, другие не должны проверяться.
    """
    mock_storage.check_and_update.side_effect = [False, True]  # Первое правило - отказ

    # Строгое: 1/10 = 0.1
    strict_rule = RateLimitRule(limit=1, period=timedelta(seconds=10))
    # Мягкое: 100/60 ~ 1.6
    soft_rule = RateLimitRule(limit=100, period=timedelta(seconds=60))

    limiter = RateLimiter(storage=mock_storage, rules=[soft_rule, strict_rule])

    is_allowed = await limiter.is_allowed("test-id")

    assert is_allowed is False
    # Убеждаемся, что была вызвана проверка только для самого строгого правила
    mock_storage.check_and_update.assert_called_once_with(strict_rule, "test-id")