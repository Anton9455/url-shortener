"""Генерация коротких кодов для ссылок."""
import secrets
import string

ALPHABET = string.ascii_letters + string.digits
DEFAULT_LENGTH = 6


def generate_code(length: int = DEFAULT_LENGTH) -> str:
    """
    Сгенерировать случайный код заданной длины.

    Использует secrets.choice — криптостойкий источник.
    Алфавит: [A-Za-z0-9].

    Raises:
        ValueError: если length <= 0.
    """
    if length <= 0:
        raise ValueError(f"length must be positive, got {length}")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
