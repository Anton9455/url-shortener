"""Тесты для GET /{code} — редирект по короткому коду."""

from app.models import Link


def _make_link(db_session, code="abc123",
                url="https://example.com/target"):
    """Хелпер: положить Link в БД."""
    link = Link(code=code, original_url=url)
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


def test_redirect_valid_code_returns_302(client, db_session):
    """GET /abc123 (есть в БД) -> 302."""
    _make_link(db_session, code="abc123")
    response = client.get("/abc123", follow_redirects=False)
    assert response.status_code == 302


def test_redirect_location_header_correct(client, db_session):
    """Location == original_url."""
    _make_link(db_session, code="abc123",
                url="https://example.com/target")
    response = client.get("/abc123", follow_redirects=False)
    assert response.headers["Location"] == "https://example.com/target"


def test_redirect_unknown_code_returns_404(client):
    """GET /zzz999 (нет в БД) -> 404."""
    response = client.get("/zzz999", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_404_returns_html(client):
    """404 должен возвращать HTML со словом 'не найдена'."""
    response = client.get("/zzz999", follow_redirects=False)
    assert response.status_code == 404
    assert "не найдена" in response.text.lower()


def test_redirect_increments_clicks(client, db_session):
    """Два GET подряд -> clicks == 2."""
    link = _make_link(db_session, code="abc123")
    client.get("/abc123", follow_redirects=False)
    client.get("/abc123", follow_redirects=False)
    db_session.refresh(link)
    assert link.clicks == 2


def test_redirect_updates_last_click_at(client, db_session):
    """GET обновляет last_click_at."""
    link = _make_link(db_session, code="abc123")
    assert link.last_click_at is None
    client.get("/abc123", follow_redirects=False)
    db_session.refresh(link)
    assert link.last_click_at is not None


def test_redirect_does_not_require_token(client, db_session):
    """GET /abc123 без X-API-Token -> не 401, а 302."""
    _make_link(db_session, code="abc123")
    response = client.get("/abc123", follow_redirects=False)
    assert response.status_code == 302


def test_redirect_invalid_code_too_short(client):
    """GET /ab (2 символа) -> 404, не доходит до БД."""
    response = client.get("/ab", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_invalid_code_too_long(client):
    """GET /abcdefghijk (11 символов) -> 404."""
    response = client.get("/abcdefghijk", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_invalid_code_chars(client):
    """GET /ab-cd! (недопустимые символы) -> 404."""
    response = client.get("/ab-cd!", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_expired_link_returns_404(client, db_session):
    """Ссылка старше TTL -> 404 и удаляется из БД."""
    from datetime import datetime, timedelta, timezone
    from app.models import Link

    old_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    link = Link(
        code="expird",
        original_url="https://ya.ru/",
        created_at=old_time,
    )
    db_session.add(link)
    db_session.commit()

    response = client.get("/expird", follow_redirects=False)
    assert response.status_code == 404

    # Проверить, что запись удалена из БД
    assert db_session.query(Link).filter_by(code="expird").first() is None


def test_redirect_fresh_link_works(client, db_session):
    """Ссылка младше TTL -> 302."""
    from app.models import Link

    link = Link(code="fresh1", original_url="https://ya.ru/")
    db_session.add(link)
    db_session.commit()

    response = client.get("/fresh1", follow_redirects=False)
    assert response.status_code == 302
