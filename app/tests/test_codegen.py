import string
import pytest
from app import codegen


def test_generate_code_default_length():
    """Тест: дефолтная длина кода - 6"""
    result = codegen.generate_code()
    assert len(result) == 6


def test_generate_code_custom_length():
    """Тест: пользовательская длина кода"""
    result = codegen.generate_code(8)
    assert len(result) == 8


def test_generate_code_alphanumeric():
    """Тест: код содержит только буквенно-цифровые символы"""
    results = [codegen.generate_code() for _ in range(100)]
    alphabet = set(string.ascii_letters + string.digits)
    for result in results:
        assert all(char in alphabet for char in result)


def test_generate_code_is_random():
    """Тест: генерация даёт уникальные значения"""
    results = [codegen.generate_code() for _ in range(100)]
    assert len(set(results)) > 90


def test_generate_code_length_negative_raises():
    """Тест: отрицательная длина вызывает ValueError"""
    with pytest.raises(ValueError):
        codegen.generate_code(-1)


def test_generate_code_length_zero_raises():
    """Тест: длина 0 вызывает ValueError"""
    with pytest.raises(ValueError):
        codegen.generate_code(0)


def test_generate_code_uses_secrets_module(monkeypatch):
    """Тест: использует secrets.choice вместо random"""
    call_count = [0]
    original_choice = __import__("secrets").choice

    def mock_choice(alphabet):
        call_count[0] += 1
        return original_choice(alphabet)

    monkeypatch.setattr(__import__("secrets"), "choice", mock_choice)

    codegen.generate_code(8)
    assert call_count[0] == 8
