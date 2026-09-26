
import pytest
from pydantic import ValidationError
from app.config import Settings


def test_config_loads_api_token_from_env(env):
    """Тест загрузки API_TOKEN из переменной окружения"""
    env.setenv("API_TOKEN", "abc")
    settings = Settings(_env_file=None)
    assert settings.api_token == "abc"


def test_config_missing_api_token_raises(env):
    """Тест: отсутствие API_TOKEN вызывает ValidationError"""
    env.delenv("API_TOKEN", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_config_default_version(env):
    """Тест: версия по умолчанию"""
    settings = Settings(_env_file=None)
    assert settings.app_version == "1.0.0"


def test_config_default_database_url(env):
    """Тест: базовый URL по умолчанию"""
    env.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.database_url == "sqlite:////data/shortener.db"


def test_config_base_url_required(env):
    """Тест: BASE_URL обязателен"""
    env.delenv("BASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
