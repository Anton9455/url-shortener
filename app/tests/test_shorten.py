"""Тесты для POST /api/shorten — часть 1: авторизация."""


def test_shorten_requires_token(client):
    """POST /api/shorten без заголовка X-API-Token -> 401."""
    response = client.post("/api/shorten", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_shorten_rejects_wrong_token(client):
    """POST /api/shorten с неверным X-API-Token -> 401."""
    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers={"X-API-Token": "wrong-token"},
    )
    assert response.status_code == 401


def test_shorten_valid_url_returns_200(client, auth_headers):
    """POST /api/shorten с валидным URL и токеном -> 200."""
    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_shorten_response_has_code(client, auth_headers):
    """body["code"] — строка длиной 6."""
    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers=auth_headers,
    )
    body = response.json()
    assert "code" in body
    assert len(body["code"]) == 6


def test_shorten_response_short_url_uses_base(client, auth_headers):
    """short_url == f"{BASE_URL}/{code}"."""
    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers=auth_headers,
    )
    body = response.json()
    assert body["short_url"] == f"https://short.test/{body['code']}"


def test_shorten_response_echoes_original(client, auth_headers):
    """body["original_url"] == входной url."""
    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers=auth_headers,
    )
    body = response.json()
    assert body["original_url"].rstrip("/") == "https://example.com"


def test_shorten_invalid_url_returns_422(client, auth_headers):
    """body={"url":"not-a-url"} -> 422."""
    response = client.post(
        "/api/shorten",
        json={"url": "not-a-url"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_shorten_missing_url_returns_422(client, auth_headers):
    """body={} -> 422."""
    response = client.post(
        "/api/shorten",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_shorten_persists_link_to_db(client, auth_headers, db_session):
    """После POST в БД появляется одна запись."""
    from app.models import Link

    client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers=auth_headers,
    )
    assert db_session.query(Link).count() == 1


def test_shorten_duplicate_url_returns_same_code(client, auth_headers):
    """Два POST с одинаковым URL -> одинаковый code."""
    payload = {"url": "https://example.com/duplicate"}
    r1 = client.post("/api/shorten", json=payload, headers=auth_headers)
    r2 = client.post("/api/shorten", json=payload, headers=auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["code"] == r2.json()["code"]


def test_shorten_duplicate_url_does_not_create_second(
    client, auth_headers, db_session,
):
    """Два POST с одинаковым URL -> в БД одна запись."""
    from app.models import Link
    payload = {"url": "https://example.com/duplicate2"}
    client.post("/api/shorten", json=payload, headers=auth_headers)
    client.post("/api/shorten", json=payload, headers=auth_headers)
    assert db_session.query(Link).count() == 1


def test_shorten_different_urls_get_different_codes(client, auth_headers):
    """Разные URL -> разные code."""
    r1 = client.post(
        "/api/shorten",
        json={"url": "https://example.com/one"},
        headers=auth_headers,
    )
    r2 = client.post(
        "/api/shorten",
        json={"url": "https://example.com/two"},
        headers=auth_headers,
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["code"] != r2.json()["code"]
