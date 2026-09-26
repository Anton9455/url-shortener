#!/bin/bash
# Диагностика стека URL Shortener.
# Запуск: bash scripts/health-check.sh
# Требует: docker compose up -d

set -uo pipefail

# PATH для cron (минимальный PATH не находит docker)
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Корень проекта — родитель scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo " URL Shortener — health check"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo

echo "--- 1. Контейнеры ---"
docker compose ps 2>&1 || echo "(docker compose недоступен)"
echo

echo "--- 2. /health ---"
if command -v curl >/dev/null 2>&1; then
    curl -s --max-time 5 http://localhost/health | python3 -m json.tool 2>/dev/null \
        || echo "health endpoint недоступен"
else
    echo "(curl не установлен)"
fi
echo

echo "--- 3. База данных ---"
if [ -f data/shortener.db ]; then
    ls -lh data/shortener.db
else
    echo "data/shortener.db не найден"
fi
echo

echo "--- 4. Последние 5 ссылок ---"
docker compose exec -T fastapi python -c "
from app.db import create_db_engine, create_session_factory
from app.models import Link
engine = create_db_engine()
Session = create_session_factory(engine)
db = Session()
rows = db.query(Link).order_by(Link.created_at.desc()).limit(5).all()
if not rows:
    print('(пусто)')
for r in rows:
    print(f'{r.code:8} clicks={r.clicks:>3} created={r.created_at} url={r.original_url[:60]}')
db.close()
" 2>/dev/null || echo "(не удалось получить список)"
echo

echo "--- 5. Использование ресурсов ---"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>&1 \
    || echo "(docker stats недоступен)"
echo

echo "--- 6. Последние 10 строк логов fastapi ---"
docker compose logs --tail=10 fastapi 2>&1 || echo "(логи недоступны)"
echo

echo "--- 7. Последние 5 строк логов nginx ---"
docker compose logs --tail=5 nginx 2>&1 || echo "(логи недоступны)"
echo

echo "=========================================="
echo " Готово: $(date '+%H:%M:%S')"
echo "=========================================="
