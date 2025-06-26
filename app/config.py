from functools import lru_cache
from pydantic import RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Типизированная конфигурация приложения, загружаемая из .env файла и переменных окружения.
    """
    REDIS_URL: SecretStr = "redis://localhost:6379"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает синглтон-экземпляр настроек."""
    return Settings()