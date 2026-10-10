# URL Shortener

Учебный проект по дисциплине «Инфраструктура и администрирование».

Сервис сокращения ссылок на FastAPI + Streamlit + Nginx,
развёрнутый в Docker Compose на собственном оборудовании.

![CI](https://github.com/Anton9455/url-shortener/actions/workflows/ci.yml/badge.svg)

## Что делает

Сервис для сокращения длинных URL: пользователь вводит ссылку,
получает короткий код, при переходе по которому происходит
редирект на оригинальный адрес. Ссылки живут 15 минут (настройка в .env), затем
автоматически удаляются.

## Информация

- Учебный проект.
- Размещён на собственном оборудовании (Proxmox VE).
- Ссылки автоматически удаляются через 15 минут
  (настраивается через `LINK_TTL_MINUTES`).

## Требования

- Linux (Debian 12+, Ubuntu 22.04+) или macOS
- Python 3.12+ (для локального запуска тестов)
- Docker Engine 20.10+
- Docker Compose v2

## Паспорт проекта

| Поле | Значение |
|---|---|
| **Git repository** | https://github.com/Anton9455/url-shortener |
| **Server OS** | Debian 13 (Trixie) |
| **Hosting type** | LXC-контейнер на Proxmox VE (домашний сервер) |
| **Public IP** | не публикуется; доступ через KeenDNS Cloud Access |
| **Application port** | 8000 (внутренний, FastAPI); 80 (внешний, nginx) |
| **Public URL** | https://url-shortener.ant-keenetic.netcraze.pro |
| **Process manager** | Docker Compose (`restart: unless-stopped`) |
| **Reverse proxy** | Nginx: маршрутизация `/api/`, `/health`, `/version`, `/{code}`, `/`; TLS-терминация на Keenetic |
| **Log command** | `docker compose logs -f fastapi` |
| **Restart command** | `docker compose restart fastapi` |

## Быстрый старт

### Автоматическая установка (рекомендуется)

    bash scripts/init.sh

Скрипт спросит внешний URL, логин и пароль Basic Auth.
Остальное (`.env`, API-токен, `.htpasswd`, `logs/`, сборка
образов, запуск, cron) — сделает сам.

### Ручная установка

Если хочется развернуть без `init.sh`:

1. Создать `.env`:
       cp .env.example .env
       # отредактировать: API_TOKEN, BASE_URL

2. Создать `.htpasswd` для Basic Auth:
       docker run --rm httpd:2.4-alpine htpasswd -nbB <login> <password> > nginx/.htpasswd

   Замени `<login>` и `<password>` на свои значения

3. Создать директорию для логов:
       mkdir -p logs

4. Запустить стек:
       docker compose up -d --build

5. (Опционально) Настроить cron для диагностики:
       bash scripts/setup-cron.sh

## Логирование

Все события пишутся в stdout контейнера fastapi
(собирается `docker compose logs`). Уровни: INFO, WARNING.

| Событие | Уровень | Пример |
|---|---|---|
| Создание ссылки | INFO | `link created: code=ABC123 url=... source=api` |
| Успешный редирект | INFO | `redirect: code=ABC123 -> https://... (clicks=N)` |
| Удаление истёкшей | INFO | `expired link removed: code=ABC123 age_min=N ttl_min=15` |
| HTTP-запрос | INFO | `GET /health 200 12.3ms` |
| Ошибка аутентификации | WARNING | `auth failed: token_prefix=wrong-12` |

## Тесты

Unit-тесты запускаются локально:

        python -m pytest app/tests -v

Интеграционные тесты требуют запущенного стека:

        docker compose up -d
        python -m pytest tests_integration -m integration -v

## Переменные окружения

Задаются в `.env` (создаётся из `.env.example`).

| Переменная | По умолчанию | Описание |
|---|---|---|
| `API_TOKEN` | — (обязательно) | Токен для доступа к API (`X-API-Token`) |
| `BASE_URL` | — (обязательно) | Базовый URL для коротких ссылок |
| `DATABASE_URL` | `sqlite:////data/shortener.db` | Подключение к БД |
| `APP_VERSION` | `1.0.0` | Версия приложения (отдаётся в `/version`) |
| `FASTAPI_URL` | `http://fastapi:8000` | URL FastAPI для UI |
| `LINK_TTL_MINUTES` | `15` | Время жизни ссылки (минуты) |

## Диагностика

### В браузере

Вкладка «Диагностика» в Streamlit UI показывает содержимое
`/logs/health.log` — файл, который создаётся на хосте по cron.
Кнопка «Обновить лог» перечитывает файл.

### В терминале на хосте

Быстрая диагностика одной командой:

    bash scripts/health-check.sh

Установка cron-задачи (один раз, на LXC):

    bash scripts/setup-cron.sh

После установки cron каждые 5 минут обновляет
`logs/health.log`, который читает UI.

### Живые логи

    docker compose logs -f fastapi    # логи API
    docker compose logs -f nginx      # логи nginx
    docker compose logs -f streamlit  # логи UI

## Проверка работоспособности

После запуска:

    # Статус сервиса и БД
    curl http://localhost/health

    # Версия приложения
    curl http://localhost/version

Документация API (Swagger UI):

    http://localhost/docs

Открыть в браузере.

## Запуск без --reload

В production uvicorn запускается без автоматической перезагрузки.
Настроено в `app/Dockerfile`:

    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

Для ручного запуска вне Docker:

    uvicorn app.main:app --host 0.0.0.0 --port 8000

## Как разрабатывался

Проект написан по методологии TDD: сначала тесты, потом
реализация. Разработка велась в формате «промт → код → проверка»
с использованием LLM-ассистентов: облачная модель для
валидации архитектурных решений и локальная модель для генерации кода.

Автор отвечал за архитектуру сервиса, постановку и декомпозицию
задач, выбор технологий и верификацию результатов.

## Состав проекта

- `app/` — FastAPI-приложение (API и редирект).
- `ui/` — Streamlit-интерфейс.
- `nginx/` — reverse proxy.
- `tests_integration/` — smoke-тесты против запущенного стека.
- `scripts/` — скрипты для диагностики и настройки cron-задач.