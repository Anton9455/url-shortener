"""Тесты для слоя работы с БД."""
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.db import init_db
from app.models import Link


def test_init_db_creates_links_table(db_engine):
    """Тест: init_db создаёт таблицу links."""
    init_db(db_engine)
    assert inspect(db_engine).has_table("links")


def test_create_link_persists(db_session):
    """Тест: создание Link сохраняется в БД."""
    link = Link(code="abc123", original_url="https://example.com")
    db_session.add(link)
    db_session.commit()
    assert link.id is not None


def test_create_link_default_clicks_zero(db_session):
    """Тест: clicks по умолчанию равен 0."""
    link = Link(code="abc123", original_url="https://example.com")
    db_session.add(link)
    db_session.commit()
    assert link.clicks == 0


def test_create_link_sets_created_at(db_session):
    """Тест: created_at устанавливается."""
    link = Link(code="abc123", original_url="https://example.com")
    db_session.add(link)
    db_session.commit()
    assert link.created_at is not None


def test_create_link_last_click_at_is_none(db_session):
    """Тест: last_click_at по умолчанию None."""
    link = Link(code="abc123", original_url="https://example.com")
    db_session.add(link)
    db_session.commit()
    assert link.last_click_at is None


def test_code_unique_constraint(db_session):
    """Тест: unique constraint на code работает."""
    link1 = Link(code="abc123", original_url="https://example.com")
    db_session.add(link1)
    db_session.commit()
    link2 = Link(code="abc123", original_url="https://example.org")
    db_session.add(link2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_get_by_code_found(db_session):
    """Тест: поиск по существующему code работает."""
    link = Link(code="abc123", original_url="https://example.com")
    db_session.add(link)
    db_session.commit()
    found = db_session.query(Link).filter_by(code="abc123").first()
    assert found is not None
    assert found.code == "abc123"


def test_get_by_code_not_found(db_session):
    """Тест: поиск несуществующего code возвращает None."""
    found = db_session.query(Link).filter_by(code="nonexistent").first()
    assert found is None
