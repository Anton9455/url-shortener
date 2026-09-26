"""Pydantic-схемы для API."""
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class HealthResponse(BaseModel):
    """Ответ эндпоинта /health."""
    status: str
    db: str
    version: str
    uptime_sec: int


class ShortenRequest(BaseModel):
    """Запрос на сокращение ссылки."""
    url: HttpUrl


class ShortenResponse(BaseModel):
    """Ответ с сокращённой ссылкой."""
    code: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    """Ответ эндпоинта /api/stats/{code}."""
    code: str
    original_url: str
    clicks: int
    created_at: datetime
    last_click_at: datetime | None


class LinkItem(BaseModel):
    """Элемент списка ссылок."""
    code: str
    original_url: str
    clicks: int
    created_at: datetime
    last_click_at: datetime | None
