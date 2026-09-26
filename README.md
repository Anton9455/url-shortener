# URL Shortener

Учебный проект по дисциплине «Инфраструктура и администрирование».

Сервис сокращения ссылок на FastAPI + Streamlit + Nginx,
развёрнутый в Docker Compose на собственном оборудовании.

## Информация

- Учебный проект, не является коммерческим сервисом.
- Размещён на собственном оборудовании (Proxmox VE).
- Ссылки автоматически удаляются через 15 минут
  (настраивается через `LINK_TTL_MINUTES`).

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

## Состав проекта

- `app/` — FastAPI-приложение (API и редирект).
- `ui/` — Streamlit-интерфейс.
- `nginx/` — reverse proxy.
- `tests_integration/` — smoke-тесты против запущенного стека.
- `scripts/` — скрипты для диагностики и настройки cron-задач.