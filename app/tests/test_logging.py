"""Тесты для middleware логирования."""

import logging


def _app_log_text(caplog) -> str:
    """Склеить сообщения всех записей от logger 'app'."""
    records = [r for r in caplog.records if r.name == "app"]
    return " ".join(r.getMessage() for r in records)


def test_middleware_logs_request(caplog, client):
    """GET /health -> в caplog есть запись, содержащая 'GET /health'."""
    response = client.get("/health")
    assert response.status_code == 200

    text = _app_log_text(caplog)
    assert "GET /health" in text


def test_middleware_logs_status_code(caplog, client):
    """GET /health -> в caplog есть '200'."""
    response = client.get("/health")
    assert response.status_code == 200

    text = _app_log_text(caplog)
    assert "200" in text


def test_middleware_logs_duration(caplog, client):
    """GET /health -> в caplog есть 'ms'."""
    response = client.get("/health")
    assert response.status_code == 200

    text = _app_log_text(caplog)
    assert "ms" in text


def test_shorten_logs_creation(caplog, client, auth_headers):
    """POST /api/shorten -> в логе есть 'link created'."""
    import logging
    caplog.set_level(logging.INFO, logger="app")

    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com/log-test"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    text = _app_log_text(caplog)
    assert "link created" in text


def test_redirect_logs_success(caplog, client, db_session):
    """GET /{code} -> в логе есть 'redirect'."""
    import logging
    from app.models import Link

    caplog.set_level(logging.INFO, logger="app")

    link = Link(code="logred", original_url="https://ya.ru/")
    db_session.add(link)
    db_session.commit()

    response = client.get("/logred", follow_redirects=False)
    assert response.status_code == 302

    text = _app_log_text(caplog)
    assert "redirect" in text


def test_redirect_logs_expiry(caplog, client, db_session):
    """GET /{code} для истёкшей -> 'expired link removed'."""
    import logging
    from datetime import datetime, timedelta, timezone
    from app.models import Link

    caplog.set_level(logging.INFO, logger="app")

    old_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    link = Link(
        code="logexp",
        original_url="https://ya.ru/",
        created_at=old_time,
    )
    db_session.add(link)
    db_session.commit()

    response = client.get("/logexp", follow_redirects=False)
    assert response.status_code == 404

    text = _app_log_text(caplog)
    assert "expired link removed" in text


def test_auth_failure_logs_warning(caplog, client):
    """POST без токена -> в логе 'auth failed'."""
    import logging
    caplog.set_level(logging.WARNING, logger="app")

    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
    )
    assert response.status_code == 401

    text = _app_log_text(caplog)
    assert "auth failed" in text
