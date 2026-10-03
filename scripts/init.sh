#!/bin/bash
# scripts/init.sh — интерактивная инициализация URL Shortener.
# Использование: bash scripts/init.sh

set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
    echo "❌ Запусти через bash: bash scripts/init.sh"
    exit 1
fi

cd "$(dirname "$0")/.."

# --- Функции ---
check_containers() {
    local running total
    running=$(docker compose ps --format json 2>/dev/null | grep -c '"State":"running"' || echo 0)
    total=$(docker compose config --services 2>/dev/null | wc -l)
    if [ "$running" -eq "$total" ] && [ "$total" -gt 0 ]; then
        echo "  Контейнеры: $running/$total running ✓"
    else
        echo "  Контейнеры: $running/$total running ⚠"
    fi
}

# --- Заголовок ---
echo "=== URL Shortener — инициализация ==="
echo

# --- Проверки окружения ---
command -v docker >/dev/null 2>&1 || { echo "❌ docker не установлен"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "❌ docker compose не установлен"; exit 1; }
echo "✓ Окружение: docker + docker compose"
echo

# --- Предупреждение ---
echo "⚠ ВНИМАНИЕ"
echo
echo "Скрипт разворачивает сервис С НУЛЯ. Если он уже был установлен,"
echo "все данные будут удалены!"
read -p "Нажми Enter для продолжения или Ctrl+C для отмены..."
echo

# --- Очистка предыдущего состояния ---
echo "→ Очищаю предыдущее состояние (если было)..."
docker compose down -v 2>/dev/null || true
rm -f .env nginx/.htpasswd 2>/dev/null || true
rm -rf logs/ 2>/dev/null || true

# Удалить старую cron-задачу (если была)
if command -v crontab >/dev/null 2>&1; then
    crontab -l 2>/dev/null | grep -v "url-shortener-health-check" | crontab - 2>/dev/null || true
fi

echo "✓ Готово"
echo

# --- .env ---
echo "Готовлю .env"
echo "Внешний URL сервиса"
read -p "URL [Enter = http://localhost]: " USER_URL
BASE_URL="${USER_URL:-http://localhost}"
cp .env.example .env
sed -i "s|^BASE_URL=.*|BASE_URL=$BASE_URL|" .env
echo

echo "API-токен (передаётся его в заголовке X-API-Token)"
read -p "Токен [Enter = сгенерировать]: " USER_TOKEN

if [ -z "$USER_TOKEN" ]; then
    if [ -r /proc/sys/kernel/random/uuid ]; then
        USER_TOKEN=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
        echo "✓ Токен сгенерирован: $USER_TOKEN"
    else
        USER_TOKEN=$(date +%s%N)
        echo "⚠ /proc/sys/kernel/random/uuid недоступен."
        echo "  Сгенерирован слабый токен: $USER_TOKEN"
        echo "  Рекомендую заменить в .env на случайную строку."
    fi
else
    echo "✓ Использую введённый токен."
fi

sed -i "s|^API_TOKEN=.*|API_TOKEN=$USER_TOKEN|" .env
echo "✓ .env создан (BASE_URL=$BASE_URL)"
echo

# --- .htpasswd ---
echo "Basic Auth"
read -p "Логин [admin]: " USER_LOGIN
USER_LOGIN="${USER_LOGIN:-admin}"

while true; do
    read -s -p "Пароль (не может быть пустым): " USER_PASS
    echo
    if [ -n "$USER_PASS" ]; then
        break
    fi
    echo "  Пароль пустой. Попробуй ещё раз."
done

docker run --rm httpd:2.4-alpine htpasswd -nbB "$USER_LOGIN" "$USER_PASS" > nginx/.htpasswd
echo "✓ nginx/.htpasswd создан (логин=$USER_LOGIN)"
echo

# --- logs/ ---
mkdir -p logs
echo "✓ Директория logs/ готова"
echo

# --- Сборка и запуск ---
echo "→ Собираю и запускаю стек (2-5 минут)..."
docker compose up -d --build
echo

echo "→ Жду, пока fastapi станет healthy (до 5 минут)..."
HEALTHY=0
for i in $(seq 1 60); do
    if docker compose ps fastapi 2>/dev/null | grep -q "healthy"; then
        HEALTHY=1
        break
    fi
    sleep 5
done

if [ "$HEALTHY" = "1" ]; then
    echo "✓ fastapi healthy"
else
    echo "⚠ fastapi не стал healthy за 5 минут. Проверь:"
    echo "    docker compose logs fastapi --tail 50"
fi
echo

# --- cron ---
CRON_STATUS="не настроен"
echo "Cron — автоматическая диагностика каждые 5 минут."
echo "Пишет результат в logs/health.log, который читает вкладка"
echo "«Диагностика» в UI."
read -p "Настроить cron? [y/N]: " USER_CRON
if [[ "${USER_CRON:-}" =~ ^[Yy]$ ]]; then
    if command -v crontab >/dev/null 2>&1; then
        bash scripts/setup-cron.sh && CRON_STATUS="настроен"
    else
        echo "⚠ crontab не установлен"
        CRON_STATUS="не настроен (нет crontab)"
    fi
fi
echo

# --- Финальный отчёт ---
echo "=========================================="
echo " URL Shortener запущен"
echo "=========================================="
echo
echo "Точка входа:"
echo "  UI:     $BASE_URL/"
echo "  Health: $BASE_URL/health"
echo
echo "Доступ:"
echo "  Логин:  $USER_LOGIN"
echo "  Пароль: $USER_PASS"
echo
echo "Статус:"
echo "  Cron:   $CRON_STATUS"
check_containers
echo
echo "Проверка вручную:"
echo "  docker compose ps"
echo "  curl http://localhost/health"
echo
echo "Диагностика:"
echo "  bash scripts/health-check.sh"
echo "=========================================="