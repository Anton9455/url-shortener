"""FastAPI-приложение URL Shortener."""
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{6}$")

from app.config import Settings
from app.codegen import generate_code
from app.db import (
    create_db_engine,
    create_session_factory,
    init_db,
)
from app.models import Link
from app.schemas import HealthResponse, LinkItem, ShortenRequest, ShortenResponse, StatsResponse

# --- логирование ---
if not logging.getLogger("app").handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
    )
logger = logging.getLogger("app")


# --- запуск ---
START_TIME = time.monotonic()
settings = Settings()
engine = create_db_engine(settings.database_url)
init_db(engine)
SessionLocal = create_session_factory(engine)

app = FastAPI(title="URL Shortener", version=settings.app_version)


def get_db():
    """Dependency: сессия БД на время запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(x_api_token: str | None = Header(default=None)):
    """Проверить X-API-Token. Бросает 401 при неверном/отсутствующем."""
    if x_api_token != settings.api_token:
        logger.warning(
            "auth failed: token_prefix=%s",
            (x_api_token or "<missing>")[:8],
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Token",
        )


# --- middleware логирования ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method, request.url.path,
        response.status_code, duration_ms,
    )
    return response


# --- эндпоинты ---
@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    """Проверка живости сервиса и БД."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except OperationalError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "db": "fail",
                "version": settings.app_version,
                "uptime_sec": int(time.monotonic() - START_TIME),
            },
        )
    return HealthResponse(
        status="ok",
        db=db_status,
        version=settings.app_version,
        uptime_sec=int(time.monotonic() - START_TIME),
    )


# --- эндпоинты ---
@app.post("/api/shorten", response_model=ShortenResponse)
def shorten(
    payload: ShortenRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    """Сократить URL. Если URL уже был — вернуть существующий код."""
    original_url = str(payload.url)

    existing = (
        db.query(Link)
        .filter(Link.original_url == original_url)
        .first()
    )
    if existing is not None:
        return ShortenResponse(
            code=existing.code,
            short_url=f"{settings.base_url}/{existing.code}",
            original_url=existing.original_url,
        )

    code = generate_code()
    link = Link(code=code, original_url=original_url)
    db.add(link)
    db.commit()
    db.refresh(link)
    logger.info(
        "link created: code=%s url=%s source=api",
        link.code,
        link.original_url,
    )
    return ShortenResponse(
        code=link.code,
        short_url=f"{settings.base_url}/{link.code}",
        original_url=link.original_url,
    )


# --- эндпоинты ---
@app.get("/api/stats/{code}", response_model=StatsResponse)
def get_stats(
    code: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    """Статистика по короткому коду."""
    link = db.query(Link).filter(Link.code == code).first()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Code '{code}' not found",
        )
    return StatsResponse(
        code=link.code,
        original_url=link.original_url,
        clicks=link.clicks,
        created_at=link.created_at,
        last_click_at=link.last_click_at,
    )


# --- эндпоинты ---
@app.get("/api/links", response_model=list[LinkItem])
def list_links(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    """Список последних ссылок (по убыванию created_at)."""
    links = (
        db.query(Link)
        .order_by(Link.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        LinkItem(
            code=link.code,
            original_url=link.original_url,
            clicks=link.clicks,
            created_at=link.created_at,
            last_click_at=link.last_click_at,
        )
        for link in links
    ]


# --- эндпоинты ---
@app.get("/{code}")
def redirect_to_original(
    code: str,
    db: Session = Depends(get_db),
):
    """Редирект по короткому коду на исходный URL."""
    if not CODE_PATTERN.match(code):
        return HTMLResponse(
            status_code=404,
            content="<html><body><h1>Ссылка не найдена</h1>"
                    "</body></html>",
        )

    link = db.query(Link).filter(Link.code == code).first()

    if link is None:
        return HTMLResponse(
            status_code=404,
            content=f"<html><body><h1>Ссылка не найдена</h1>"
                    f"<p>Код '{code}' не существует.</p>"
                    f"</body></html>",
        )

    age = datetime.now(timezone.utc) - link.created_at.replace(tzinfo=timezone.utc)
    if age > timedelta(minutes=settings.link_ttl_minutes):
        db.delete(link)
        db.commit()
        logger.info(
            "expired link removed: code=%s age_min=%d ttl_min=%d",
            code,
            int(age.total_seconds() // 60),
            settings.link_ttl_minutes,
        )
        return HTMLResponse(
            status_code=404,
            content=(
                f"<html><body><h1>Ссылка истекла</h1>"
                f"<p>Код '{code}' был действителен "
                f"{settings.link_ttl_minutes} минут.</p>"
                f"</body></html>"
            ),
        )

    link.clicks += 1
    link.last_click_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(
        "redirect: code=%s -> %s (clicks=%d)",
        link.code,
        link.original_url,
        link.clicks,
    )
    return RedirectResponse(
        url=link.original_url,
        status_code=302,
    )

