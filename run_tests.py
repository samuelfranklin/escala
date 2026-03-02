#!/usr/bin/env python3
"""
Script manual de testes para disponibilidade.
Não depende de pytest - testa funções puras diretamente.
"""

import sys
from datetime import date, timedelta

# Adicionar projeto ao path
sys.path.insert(0, '/home/samuel/projects/escala')

from helpers.disponibilidade import (
    parse_date_string,
    format_date_to_display,
    is_date_in_future,
    validate_restriction_date,
    MemberRestrictionError,
)


def test_parse_date_string():
    """Testes para parse_date_string."""
    print("=" * 60)
    print("TESTE: parse_date_string()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Teste 1: Data valida
    try:
        result = parse_date_string("01/01/2025")
        assert result == date(2025, 1, 1), f"Expected date(2025, 1, 1), got {result}"
        print("✓ parse_valid_date_returns_date_object")
        tests_passed += 1
    except Exception as e:
        print(f"✗ parse_valid_date_returns_date_object: {e}")
        tests_failed += 1

    # Teste 2: Data com espaços
    try:
        result = parse_date_string("  01/01/2025  ")
        assert result == date(2025, 1, 1)
        print("✓ parse_leading_trailing_spaces_should_work")
        tests_passed += 1
    except Exception as e:
        print(f"✗ parse_leading_trailing_spaces_should_work: {e}")
        tests_failed += 1

    # Teste 3: Formato invalido
    try:
        parse_date_string("2025-01-01")
        print(f"✗ parse_invalid_format_raises_error: Should raise error")
        tests_failed += 1
    except MemberRestrictionError as e:
        if "DD/MM/YYYY" in str(e):
            print("✓ parse_invalid_format_raises_error")
            tests_passed += 1
        else:
            print(f"✗ parse_invalid_format_raises_error: Wrong error message: {e}")
            tests_failed += 1

    # Teste 4: Data invalida
    try:
        parse_date_string("31/02/2025")
        print(f"✗ parse_invalid_date_raises_error: Should raise error")
        tests_failed += 1
    except MemberRestrictionError:
        print("✓ parse_invalid_date_raises_error")
        tests_passed += 1

    # Teste 5: String vazia
    try:
        parse_date_string("")
        print(f"✗ parse_empty_string_raises_error: Should raise error")
        tests_failed += 1
    except MemberRestrictionError:
        print("✓ parse_empty_string_raises_error")
        tests_passed += 1

    return tests_passed, tests_failed


def test_format_date_to_display():
    """Testes para format_date_to_display."""
    print("\n" + "=" * 60)
    print("TESTE: format_date_to_display()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Teste 1: Data simples
    try:
        result = format_date_to_display(date(2025, 1, 1))
        assert result == "01/01/2025", f"Expected '01/01/2025', got '{result}'"
        print("✓ format_date_object_to_string")
        tests_passed += 1
    except Exception as e:
        print(f"✗ format_date_object_to_string: {e}")
        tests_failed += 1

    # Teste 2: Padding dia
    try:
        result = format_date_to_display(date(2025, 1, 5))
        assert result == "05/01/2025"
        print("✓ format_date_with_single_digit_day_is_padded")
        tests_passed += 1
    except Exception as e:
        print(f"✗ format_date_with_single_digit_day_is_padded: {e}")
        tests_failed += 1

    # Teste 3: Padding mês
    try:
        result = format_date_to_display(date(2025, 3, 15))
        assert result == "15/03/2025"
        print("✓ format_date_with_single_digit_month_is_padded")
        tests_passed += 1
    except Exception as e:
        print(f"✗ format_date_with_single_digit_month_is_padded: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_is_date_in_future():
    """Testes para is_date_in_future."""
    print("\n" + "=" * 60)
    print("TESTE: is_date_in_future()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Teste 1: Data futura
    try:
        tomorrow = date.today() + timedelta(days=1)
        result = is_date_in_future(tomorrow)
        assert result is True
        print("✓ future_date_returns_true")
        tests_passed += 1
    except Exception as e:
        print(f"✗ future_date_returns_true: {e}")
        tests_failed += 1

    # Teste 2: Data de hoje
    try:
        today = date.today()
        result = is_date_in_future(today)
        assert result is True
        print("✓ today_returns_true")
        tests_passed += 1
    except Exception as e:
        print(f"✗ today_returns_true: {e}")
        tests_failed += 1

    # Teste 3: Data no passado
    try:
        yesterday = date.today() - timedelta(days=1)
        result = is_date_in_future(yesterday)
        assert result is False
        print("✓ yesterday_returns_false")
        tests_passed += 1
    except Exception as e:
        print(f"✗ yesterday_returns_false: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_validate_restriction_date():
    """Testes para validate_restriction_date."""
    print("\n" + "=" * 60)
    print("TESTE: validate_restriction_date()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Teste 1: Data valida no futuro
    try:
        future_date_str = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        result = validate_restriction_date(future_date_str)
        assert isinstance(result, date)
        print("✓ valid_future_date_returns_date")
        tests_passed += 1
    except Exception as e:
        print(f"✗ valid_future_date_returns_date: {e}")
        tests_failed += 1

    # Teste 2: Data no passado rejeitada
    try:
        past_date_str = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        validate_restriction_date(past_date_str)
        print(f"✗ past_date_raises_error: Should raise error")
        tests_failed += 1
    except MemberRestrictionError as e:
        if "passado" in str(e).lower() or "past" in str(e).lower():
            print("✓ past_date_raises_error")
            tests_passed += 1
        else:
            print(f"✗ past_date_raises_error: Wrong error message: {e}")
            tests_failed += 1

    # Teste 3: Formato invalido rejeitado
    try:
        validate_restriction_date("invalid-date")
        print(f"✗ invalid_format_raises_error: Should raise error")
        tests_failed += 1
    except MemberRestrictionError as e:
        if "formato" in str(e).lower() or "format" in str(e).lower():
            print("✓ invalid_format_raises_error")
            tests_passed += 1
        else:
            print(f"✗ invalid_format_raises_error: Wrong error message: {e}")
            tests_failed += 1

    return tests_passed, tests_failed


def main():
    """Roda todos os testes."""
    total_passed = 0
    total_failed = 0

    p, f = test_parse_date_string()
    total_passed += p
    total_failed += f

    p, f = test_format_date_to_display()
    total_passed += p
    total_failed += f

    p, f = test_is_date_in_future()
    total_passed += p
    total_failed += f

    p, f = test_validate_restriction_date()
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✓ Testes passaram: {total_passed}")
    print(f"✗ Testes falharam: {total_failed}")
    print(f"Total: {total_passed + total_failed}")

    coverage_percent = int((total_passed / (total_passed + total_failed)) * 100)
    print(f"Coverage: {coverage_percent}%")

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
