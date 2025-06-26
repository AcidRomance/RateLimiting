from datetime import timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI

from apex_limiter.core.rules import RateLimitRule
from apex_limiter.framework.fastapi import (
    get_redis_client,
    rate_limiter_dependency,
    rate_limit_checker
)

# --- Определение правил для различных эндпоинтов ---
protected_rules = [RateLimitRule(limit=5, period=timedelta(seconds=10))]
critical_rules = [RateLimitRule(limit=2, period=timedelta(seconds=20))]

# --- Создание зависимостей с конкретными правилами ---
ProtectedLimiter = Annotated[
    None,
    Depends(rate_limit_checker),
    Depends(rate_limiter_dependency(rules=protected_rules))
]
CriticalLimiter = Annotated[
    None,
    Depends(rate_limit_checker),
    Depends(rate_limiter_dependency(rules=critical_rules))
]

# --- Инициализация приложения ---
app = FastAPI(
    title="Apex Rate Limiter Demo",
    description="Пример использования библиотеки ApexLimiter с FastAPI",
)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Корректно закрываем соединение с Redis при остановке приложения."""
    redis_client = get_redis_client()
    await redis_client.close()

@app.get("/")
async def public_route() -> dict[str, Any]:
    return {"message": "This route is public and has no rate limits."}


@app.get("/protected", dependencies=[ProtectedLimiter])
async def protected_route() -> dict[str, Any]:
    return {
        "message": "You can access this 5 times every 10 seconds.",
        "rules": protected_rules,
    }


@app.get("/critical", dependencies=[CriticalLimiter])
async def critical_route() -> dict[str, Any]:
    return {
        "message": "This is a critical endpoint. You can access it 2 times every 20 seconds.",
        "rules": critical_rules,
    }