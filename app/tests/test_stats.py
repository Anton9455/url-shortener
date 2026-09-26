"""Тесты для GET /api/stats/{code}."""

from app.models import Link


def _make_link(db_session, code="abc123",
                url="https://example.com/target"):
    """Хелпер: положить Link в БД."""
    link = Link(code=code, original_url=url)
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


def test_stats_requires_token(client, db_session):
    """GET /api/stats/abc123 без X-API-Token -> 401."""
    _make_link(db_session, code="abc123")
    response = client.get("/api/stats/abc123")
    assert response.status_code == 401


def test_stats_unknown_code_returns_404(client, auth_headers):
    """GET /api/stats/zzz999 (нет в БД) -> 404."""
    response = client.get("/api/stats/zzz999", headers=auth_headers)
    assert response.status_code == 404


def test_stats_returns_all_fields(client, auth_headers, db_session):
    """Ответ содержит все поля из StatsResponse."""
    _make_link(db_session, code="abc123")
    response = client.get("/api/stats/abc123", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    for field in ("code", "original_url", "clicks",
                  "created_at", "last_click_at"):
        assert field in body, f"missing field: {field}"


def test_stats_returns_correct_clicks(client, auth_headers, db_session):
    """3 редиректа -> clicks == 3."""
    _make_link(db_session, code="abc123")
    for _ in range(3):
        client.get("/abc123", follow_redirects=False)
    response = client.get("/api/stats/abc123", headers=auth_headers)
    assert response.json()["clicks"] == 3


def test_stats_returns_last_click_at(client, auth_headers, db_session):
    """После редиректа last_click_at не None."""
    _make_link(db_session, code="abc123")
    client.get("/abc123", follow_redirects=False)
    response = client.get("/api/stats/abc123", headers=auth_headers)
    body = response.json()
    assert body["last_click_at"] is not None


def test_stats_created_at_iso_format(client, auth_headers, db_session):
    """created_at — ISO-8601 строка."""
    _make_link(db_session, code="abc123")
    response = client.get("/api/stats/abc123", headers=auth_headers)
    body = response.json()
    # Пример: "2026-09-13T18:00:24.890522"
    assert isinstance(body["created_at"], str)
    assert "T" in body["created_at"]
