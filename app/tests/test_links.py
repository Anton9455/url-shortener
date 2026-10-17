"""Тесты для GET /api/links."""

from datetime import datetime, timedelta, timezone

from app.models import Link


def _make_link(db_session, code, url="https://example.com/x",
                created_at=None):
    """Хелпер: положить Link в БД с опциональным created_at."""
    link = Link(code=code, original_url=url)
    if created_at is not None:
        link.created_at = created_at
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


def test_links_requires_token(client):
    """GET /api/links без X-API-Token -> 401."""
    response = client.get("/api/links")
    assert response.status_code == 401


def test_links_empty_db_returns_empty_list(client, auth_headers):
    """Пустая БД -> []."""
    response = client.get("/api/links", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_links_returns_all_links(client, auth_headers, db_session):
    """3 ссылки в БД -> 3 в ответе."""
    _make_link(db_session, code="aaa111", url="https://a.com/")
    _make_link(db_session, code="bbb222", url="https://b.com/")
    _make_link(db_session, code="ccc333", url="https://c.com/")
    response = client.get("/api/links", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_links_ordered_by_created_desc(client, auth_headers, db_session):
    """Свежие ссылки — первыми."""
    now = datetime.now(timezone.utc)
    _make_link(db_session, code="old111", url="https://old.com/",
                created_at=now - timedelta(minutes=10))
    _make_link(db_session, code="mid222", url="https://mid.com/",
                created_at=now - timedelta(minutes=5))
    _make_link(db_session, code="new333", url="https://new.com/",
                created_at=now)
    response = client.get("/api/links", headers=auth_headers)
    body = response.json()
    assert [item["code"] for item in body] == ["new333", "mid222", "old111"]


def test_links_respects_limit_param(client, auth_headers, db_session):
    """?limit=2 при 5 ссылках -> 2 в ответе."""
    for i in range(5):
        _make_link(db_session, code=f"abc{i:03d}",
                    url=f"https://x{i}.com/")
    response = client.get("/api/links?limit=2", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_links_limit_default_50(client, auth_headers, db_session):
    """60 ссылок -> в ответе 50 (дефолт)."""
    for i in range(60):
        _make_link(db_session, code=f"lk{i:04d}",
                    url=f"https://y{i}.com/")
    response = client.get("/api/links", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 50


def test_links_excludes_expired(client, auth_headers, db_session):
    """Истёкшие ссылки не показываются в /api/links."""
    from datetime import datetime, timedelta, timezone
    from app.models import Link

    now = datetime.now(timezone.utc)
    fresh = Link(code="fresh1", original_url="https://fresh.com/",
                 created_at=now)
    old = Link(code="old123", original_url="https://old.com/",
               created_at=now - timedelta(minutes=30))
    db_session.add_all([fresh, old])
    db_session.commit()

    response = client.get("/api/links", headers=auth_headers)
    assert response.status_code == 200
    codes = [item["code"] for item in response.json()]
    assert "fresh1" in codes
    assert "old123" not in codes


def test_links_returns_only_fresh(client, auth_headers, db_session):
    """Все возвращённые ссылки младше TTL."""
    from datetime import datetime, timedelta, timezone
    from app.models import Link

    now = datetime.now(timezone.utc)
    for i in range(3):
        db_session.add(Link(
            code=f"new{i:03d}",
            original_url=f"https://new{i}.com/",
            created_at=now - timedelta(minutes=i),
        ))
    db_session.add(Link(
        code="exp000",
        original_url="https://exp.com/",
        created_at=now - timedelta(minutes=60),
    ))
    db_session.commit()

    response = client.get("/api/links", headers=auth_headers)
    body = response.json()
    assert len(body) == 3
    assert all(item["code"] != "exp000" for item in body)