"""Тесты для эндпоинта /health."""

import pytest


def test_health_returns_200(client):
    """GET /health -> 200"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client):
    """body["status"] == "ok" """
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_db_ok(client):
    """body["db"] == "ok" """
    response = client.get("/health")
    data = response.json()
    assert data["db"] == "ok"


def test_health_returns_version(client):
    """body["version"] отражает APP_VERSION из окружения."""
    from app.main import settings
    response = client.get("/health")
    data = response.json()
    assert data["version"] == settings.app_version


def test_health_returns_uptime_field(client):
    """"uptime_sec" in body and body["uptime_sec"] >= 0"""
    response = client.get("/health")
    data = response.json()
    assert "uptime_sec" in data
    assert data["uptime_sec"] >= 0


def test_health_returns_503_on_db_failure():
    """status_code == 503, body["status"] == "error"."""
    from fastapi.testclient import TestClient
    from sqlalchemy.exc import OperationalError
    from app.main import app as fastapi_app, get_db

    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("boom", None, None)
        def close(self):
            pass

    def failing_db():
        yield BrokenSession()

    fastapi_app.dependency_overrides[get_db] = failing_db
    try:
        client = TestClient(fastapi_app)
        resp = client.get("/health")
        assert resp.status_code == 503
        assert resp.json()["status"] == "error"
    finally:
        fastapi_app.dependency_overrides.clear()


def test_health_does_not_require_token(client):
    """GET /health without X-API-Token header -> 200"""
    response = client.get("/health")
    assert response.status_code == 200
