import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import create_session_factory
from app.models import Base

@pytest.fixture(scope="session", autouse=True)
def _set_env_for_imports():
    """Устанавливает переменные окружения ДО импорта app.main."""
    import os
    os.environ.setdefault("API_TOKEN", "test-token-123")
    os.environ.setdefault("BASE_URL", "https://short.test")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("APP_VERSION", "1.0.0")


@pytest.fixture
def client(db_session, caplog):
    """TestClient с подменой get_db и настроенным caplog."""
    import logging
    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app, get_db

    caplog.set_level(logging.INFO, logger="app")

    def override_get_db():
        yield db_session
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def env(monkeypatch):
    """Устанавливает обязательные переменные окружения для Settings()."""
    monkeypatch.setenv("API_TOKEN", "test-token-123")
    monkeypatch.setenv("BASE_URL", "https://short.test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("APP_VERSION", "1.0.0")
    return monkeypatch


@pytest.fixture
def api_token():
    return "test-token-123"


@pytest.fixture
def auth_headers(api_token):
    return {"X-API-Token": api_token}


@pytest.fixture
def db_engine():
    """In-memory SQLite с одним соединением на весь тест."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Сессия БД с rollback после каждого теста."""
    factory = create_session_factory(db_engine)
    session = factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()



