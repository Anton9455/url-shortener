#!/bin/bash
# Установка cron-задачи для health-check URL Shortener.
# Запуск: bash scripts/setup-cron.sh
# Идемпотентен: повторный запуск обновляет задачу, не плодит дубли.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/health.log"
HEALTH_SCRIPT="$PROJECT_DIR/scripts/health-check.sh"
CRON_MARKER="# url-shortener-health-check"
CRON_LINE="*/5 * * * * cd $PROJECT_DIR && bash scripts/health-check.sh > $LOG_FILE 2>&1 $CRON_MARKER"

echo "=== Установка cron для URL Shortener ==="
echo "Проект:    $PROJECT_DIR"
echo "Скрипт:    $HEALTH_SCRIPT"
echo "Лог:       $LOG_FILE"
echo "Интервал:  каждые 5 минут"
echo

if ! command -v crontab >/dev/null 2>&1; then
    echo "ОШИБКА: crontab не установлен."
    echo "Установите: sudo apt update && sudo apt install -y cron"
    echo "Затем:      sudo systemctl enable --now cron"
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ПРЕДУПРЕЖДЕНИЕ: docker не найден в PATH."
    echo "Cron запускается с минимальным PATH, скрипт экспортирует свой."
fi

if [ ! -f "$HEALTH_SCRIPT" ]; then
    echo "ОШИБКА: $HEALTH_SCRIPT не найден."
    exit 1
fi

mkdir -p "$PROJECT_DIR/logs"
touch "$LOG_FILE"

if crontab -l 2>/dev/null | grep -qF "$CRON_MARKER"; then
    echo "Задача уже установлена. Обновляем..."
    crontab -l 2>/dev/null | grep -vF "$CRON_MARKER" | crontab -
fi

( crontab -l 2>/dev/null; echo "$CRON_LINE" ) | crontab -

echo "✓ Cron-задача установлена."
echo
echo "Текущий crontab (последние строки):"
crontab -l | tail -3
echo
echo "Проверка через 5 минут:"
echo "  cat $LOG_FILE"
echo
echo "Ручной запуск сейчас:"
echo "  cd $PROJECT_DIR && bash scripts/health-check.sh > logs/health.log 2>&1"
