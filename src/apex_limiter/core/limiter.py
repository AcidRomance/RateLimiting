from apex_limiter.core.rules import RateLimitRule
from apex_limiter.storage.base import IStorage


class RateLimiter:
    """
    Основной класс, управляющий логикой ограничения скорости.
    Он применяет набор правил к идентификатору, используя указанное хранилище.
    """

    def __init__(self, storage: IStorage, rules: list[RateLimitRule]):
        if not rules:
            raise ValueError("RateLimiter must be initialized with at least one rule.")
        self._storage = storage
        # Сортируем правила от самого строгого к самому мягкому для быстрой проверки
        self._rules = sorted(rules, key=lambda r: r.period_seconds / r.limit)

    async def is_allowed(self, identifier: str) -> bool:
        """
        Проверяет, разрешен ли запрос для данного идентификатора.

        Итерируется по всем правилам. Если хотя бы одно правило нарушено,
        запрос немедленно отклоняется.

        Args:
            identifier: Уникальный идентификатор клиента.

        Returns:
            True, если запрос разрешен, иначе False.
        """
        for rule in self._rules:
            if not await self._storage.check_and_update(rule, identifier):
                # Если хотя бы одно правило нарушено, сразу возвращаем False
                return False
        return True