"""Smoke-тесты против запущенного стека через nginx.

Требуют: docker compose up -d.
Запуск:  pytest tests_integration -m integration -v
"""
import uuid

import httpx
import pytest

pytestmark = pytest.mark.integration


def test_nginx_health_endpoint(base_url):
    """GET /health -> 200, JSON со status=ok."""
    r = httpx.get(f"{base_url}/health", timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"


def test_nginx_streamlit_requires_basic_auth(base_url):
    """GET / без кредов -> 401."""
    r = httpx.get(f"{base_url}/", timeout=5.0)
    assert r.status_code == 401


def test_nginx_streamlit_accepts_basic_auth(base_url, basic_auth):
    """GET / с корректным Basic Auth -> 200."""
    r = httpx.get(f"{base_url}/", auth=basic_auth, timeout=10.0)
    assert r.status_code == 200


def test_nginx_api_requires_token(base_url):
    """POST /api/shorten без X-API-Token -> 401."""
    r = httpx.post(
        f"{base_url}/api/shorten",
        json={"url": "https://example.com"},
        timeout=5.0,
    )
    assert r.status_code == 401


def test_nginx_full_flow(base_url, auth_headers):
    """POST /api/shorten -> GET /{code} -> 302, Location совпадает.

    Уникальный URL через uuid — чтобы дедупликация не находила
    ссылку с истёкшим TTL от предыдущих запусков.
    """
    unique_suffix = uuid.uuid4().hex[:12]
    target = f"https://example.com/integration-{unique_suffix}"

    r = httpx.post(
        f"{base_url}/api/shorten",
        json={"url": target},
        headers=auth_headers,
        timeout=5.0,
    )
    assert r.status_code == 200
    code = r.json()["code"]

    r2 = httpx.get(
        f"{base_url}/{code}",
        follow_redirects=False,
        timeout=5.0,
    )
    assert r2.status_code == 302
    assert r2.headers["location"] == target
