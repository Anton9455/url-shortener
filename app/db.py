"""Слой работы с базой данных."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.models import Base


def create_db_engine(database_url: str | None = None) -> Engine:
    """Создать engine по URL (по умолчанию — из Settings)."""
    url = database_url or Settings().database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Фабрика сессий для указанного engine."""
    return sessionmaker(bind=engine, autoflush=False,
                        autocommit=False, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    """Создать все таблицы, если их нет."""
    Base.metadata.create_all(bind=engine)
