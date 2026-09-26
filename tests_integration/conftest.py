"""Фикстуры для интеграционных тестов."""
import os

import pytest

BASE_URL = os.environ.get("SHORTENER_URL", "http://localhost")
API_TOKEN = os.environ.get("SHORTENER_TOKEN", "dev-token-change-me")
BASIC_AUTH = ("admin", "shortener2026")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def api_token():
    return API_TOKEN


@pytest.fixture(scope="session")
def auth_headers(api_token):
    return {"X-API-Token": api_token}


@pytest.fixture(scope="session")
def basic_auth():
    return BASIC_AUTH