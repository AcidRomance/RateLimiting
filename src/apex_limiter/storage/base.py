from abc import ABC, abstractmethod
from typing import Protocol

from apex_limiter.core.rules import RateLimitRule


class IStorage(Protocol):
    """
    Интерфейс (Протокол) для хранилища состояния Rate Limiter.
    Определяет контракт, которому должны следовать все реализации хранилищ.
    """

    @abstractmethod
    async def check_and_update(
        self,
        rule: RateLimitRule,
        identifier: str,
    ) -> bool:
        """
        Атомарно проверяет, превышен ли лимит для данного идентификатора,
        и обновляет состояние (добавляет метку текущего запроса).

        Args:
            rule: Правило ограничения.
            identifier: Уникальный идентификатор клиента (IP, user ID, и т.д.).

        Returns:
            True, если запрос разрешен (лимит не превышен), иначе False.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Закрывает соединения с хранилищем."""
        ...