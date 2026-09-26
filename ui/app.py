"""Streamlit UI для URL Shortener."""
import os
from pathlib import Path
from datetime import datetime

import httpx
import streamlit as st

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://fastapi:8000")
API_TOKEN = os.environ.get("API_TOKEN", "")
HEALTH_LOG_PATH = Path("/logs/health.log")

st.set_page_config(page_title="URL Shortener", page_icon="🔗")
st.title("🔗 URL Shortener")

if not API_TOKEN:
    st.error("API_TOKEN не задан. Проверь .env и переменные окружения.")
    st.stop()

HEADERS = {"X-API-Token": API_TOKEN}

tab_shorten, tab_stats, tab_health, tab_diag = st.tabs(
    ["Сократить", "Статистика", "Health", "Диагностика"]
)

with tab_shorten:
    st.subheader("Сократить ссылку")
    url = st.text_input("Длинный URL", placeholder="https://example.com/very/long/path")
    if st.button("Сократить", type="primary"):
        if not url:
            st.warning("Введи URL")
        else:
            try:
                r = httpx.post(
                    f"{FASTAPI_URL}/api/shorten",
                    json={"url": url},
                    headers=HEADERS,
                    timeout=10.0,
                )
                if r.status_code == 200:
                    data = r.json()
                    st.success("Готово!")
                    st.code(data["short_url"], language=None)
                    st.caption(f"Оригинал: {data['original_url']}")
                elif r.status_code == 401:
                    st.error("Неверный API_TOKEN")
                elif r.status_code == 422:
                    st.error("Некорректный URL")
                else:
                    st.error(f"Ошибка {r.status_code}: {r.text}")
            except httpx.RequestError as e:
                st.error(f"Не удалось связаться с API: {e}")

with tab_stats:
    st.subheader("Статистика по ссылкам")
    if st.button("Обновить"):
        st.rerun()
    try:
        r = httpx.get(
            f"{FASTAPI_URL}/api/links",
            headers=HEADERS,
            timeout=10.0,
        )
        if r.status_code == 200:
            links = r.json()
            if not links:
                st.info("Пока нет ни одной ссылки")
            else:
                st.dataframe(
                    links,
                    use_container_width=True,
                    hide_index=True,
                )
        elif r.status_code == 401:
            st.error("Неверный API_TOKEN")
        else:
            st.error(f"Ошибка {r.status_code}")
    except httpx.RequestError as e:
        st.error(f"Не удалось связаться с API: {e}")

with tab_health:
    st.subheader("Состояние сервиса")
    if st.button("Проверить"):
    try:
        r = httpx.get(f"{FASTAPI_URL}/health", timeout=5.0)
        st.json(r.json())
    except httpx.RequestError as e:
        st.error(f"API недоступен: {e}")

with tab_diag:
    st.subheader("Диагностика системы")
    st.caption(
        "Лог собирается на хосте по расписанию (cron, каждые 5 минут). "
        "Streamlit только отображает содержимое файла."
    )

    if st.button("Обновить лог", key="refresh_health_log"):
        st.rerun()

    if not HEALTH_LOG_PATH.exists():
        st.info(
            "Лог ещё не создан. Настройте cron на хосте:\n\n"
            "```bash\nbash scripts/setup-cron.sh\n```\n\n"
            "Или запустите вручную:\n\n"
            "```bash\nbash scripts/health-check.sh > logs/health.log 2>&1\n```"
        )
    else:
        mtime = datetime.fromtimestamp(HEALTH_LOG_PATH.stat().st_mtime)
        age_sec = (datetime.now() - mtime).total_seconds()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Обновлён", mtime.strftime("%H:%M:%S"))
        with col2:
            if age_sec < 360:
                st.metric("Возраст", f"{int(age_sec)} сек",
                          delta="свежий")
            else:
                st.metric("Возраст", f"{int(age_sec // 60)} мин",
                          delta="устарел", delta_color="inverse")

        try:
            content = HEALTH_LOG_PATH.read_text(encoding="utf-8")
            st.code(content, language="bash")
        except OSError as e:
            st.error(f"Не удалось прочитать лог: {e}")

st.divider()
st.caption(
    "🎓 Учебный проект. Не для коммерческого использования. "
    "Ссылки автоматически удаляются через 15 минут."
)