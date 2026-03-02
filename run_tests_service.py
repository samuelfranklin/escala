#!/usr/bin/env python3
"""
Script manual de testes para DisponibilidadeService.
Testa integração com BD sem depender de pytest.
"""

import sys
import os
import uuid
from datetime import date, timedelta

# Adicionar projeto ao path
sys.path.insert(0, '/home/samuel/projects/escala')

# Usar BD de teste
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from infra.database import Member, session_scope, create_tables
from services.disponibilidade_service import DisponibilidadeService


# Criar BD para testes na primeira chamada
_DB_CREATED = False


def setup_test_db():
    """Cria BD de teste e retorna ID de um membro de teste com ID único."""
    global _DB_CREATED
    
    if not _DB_CREATED:
        create_tables()
        _DB_CREATED = True
    
    # Usar ID único para cada teste
    member_id = f"test-member-{uuid.uuid4().hex[:8]}"
    
    with session_scope() as session:
        member = Member(id=member_id, name=f"João Teste {member_id}", status=True)
        session.add(member)
        session.flush()
    
    return member_id


def test_create_restriction():
    """Testes para criar restrição."""
    print("=" * 60)
    print("TESTE: DisponibilidadeService.create_restriction()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0
    
    member_id = setup_test_db()

    # Teste 1: Criar com data valida
    try:
        future_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")
        result = DisponibilidadeService.create_restriction(
            member_id=member_id,
            date_str=future_date_str,
            description="Férias",
        )
        
        assert result["success"] is True
        assert "criada" in result["message"].lower()
        assert result["restriction_id"] is not None
        
        print("✓ create_restriction_with_valid_date")
        tests_passed += 1
    except Exception as e:
        print(f"✗ create_restriction_with_valid_date: {e}")
        tests_failed += 1

    # Teste 2: Criar com data no passado (deve falhar)
    try:
        past_date_str = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        result = DisponibilidadeService.create_restriction(
            member_id=member_id,
            date_str=past_date_str,
            description="Passado",
        )
        
        assert result["success"] is False
        assert "passado" in result["message"].lower() or "past" in result["message"].lower()
        
        print("✓ create_restriction_with_past_date_fails")
        tests_passed += 1
    except Exception as e:
        print(f"✗ create_restriction_with_past_date_fails: {e}")
        tests_failed += 1

    # Teste 3: Criar para membro inexistente (deve falhar)
    try:
        result = DisponibilidadeService.create_restriction(
            member_id="nonexistent-id",
            date_str=(date.today() + timedelta(days=1)).strftime("%d/%m/%Y"),
            description="Teste",
        )
        
        assert result["success"] is False
        assert "não encontrado" in result["message"].lower()
        
        print("✓ create_restriction_for_nonexistent_member_fails")
        tests_passed += 1
    except Exception as e:
        print(f"✗ create_restriction_for_nonexistent_member_fails: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_remove_restriction():
    """Testes para remover restrição."""
    print("\n" + "=" * 60)
    print("TESTE: DisponibilidadeService.remove_restriction()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0
    
    member_id = setup_test_db()

    # Teste 1: Remover restrição existente
    try:
        # Criar antes
        future_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")
        create_result = DisponibilidadeService.create_restriction(
            member_id=member_id,
            date_str=future_date_str,
            description="A remover",
        )
        assert create_result["success"] is True
        
        # Remover
        result = DisponibilidadeService.remove_restriction(
            member_id=member_id,
            date_str=future_date_str,
        )
        
        assert result["success"] is True
        assert "removida" in result["message"].lower()
        
        print("✓ remove_existing_restriction")
        tests_passed += 1
    except Exception as e:
        print(f"✗ remove_existing_restriction: {e}")
        tests_failed += 1

    # Teste 2: Remover inexistente (deve falhar)
    try:
        # NEW member sem nenhuma restrição
        member_id_2 = setup_test_db()
        some_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")
        result = DisponibilidadeService.remove_restriction(
            member_id=member_id_2,
            date_str=some_date_str,
        )
        
        assert result["success"] is False, f"Should have failed but got success: {result}"
        assert "não encontrada" in result["message"].lower(), f"Wrong error message: {result['message']}"
        
        print("✓ remove_nonexistent_restriction_fails")
        tests_passed += 1
    except Exception as e:
        print(f"✗ remove_nonexistent_restriction_fails: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_get_restrictions():
    """Testes para listar restrições."""
    print("\n" + "=" * 60)
    print("TESTE: DisponibilidadeService.get_restrictions_by_member()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0
    
    member_id = setup_test_db()

    # Teste 1: Listar multiplas restrições em ordem
    try:
        # Criar varias
        dates = [date.today() + timedelta(days=i) for i in [1, 5, 3, 10]]
        for d in dates:
            date_str = d.strftime("%d/%m/%Y")
            DisponibilidadeService.create_restriction(
                member_id=member_id,
                date_str=date_str,
                description=f"Restrição {d}",
            )
        
        # Listar
        restrictions = DisponibilidadeService.get_restrictions_by_member(member_id)
        
        assert len(restrictions) == 4
        
        # Verificar ordem
        dates_from_result = [r["date"] for r in restrictions]
        assert dates_from_result == sorted(dates_from_result)
        
        # Verificar campos
        for r in restrictions:
            assert "id" in r
            assert "date" in r
            assert "date_display" in r
            assert "description" in r
            assert isinstance(r["date"], date)
        
        print("✓ get_restrictions_for_member_with_multiple_restrictions")
        tests_passed += 1
    except Exception as e:
        print(f"✗ get_restrictions_for_member_with_multiple_restrictions: {e}")
        tests_failed += 1

    # Teste 2: Membro sem restrições
    try:
        member_id_2 = setup_test_db()
        restrictions = DisponibilidadeService.get_restrictions_by_member(member_id_2)
        
        assert restrictions == []
        
        print("✓ get_restrictions_for_member_with_no_restrictions")
        tests_passed += 1
    except Exception as e:
        print(f"✗ get_restrictions_for_member_with_no_restrictions: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_is_member_available():
    """Testes para verificar disponibilidade."""
    print("\n" + "=" * 60)
    print("TESTE: DisponibilidadeService.is_member_available_on_date()")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0
    
    member_id = setup_test_db()

    # Teste 1: Member disponível (sem restrição)
    try:
        check_date = date.today() + timedelta(days=1)
        is_available = DisponibilidadeService.is_member_available_on_date(
            member_id=member_id,
            check_date=check_date,
        )
        
        assert is_available is True
        
        print("✓ member_available_without_restriction")
        tests_passed += 1
    except Exception as e:
        print(f"✗ member_available_without_restriction: {e}")
        tests_failed += 1

    # Teste 2: Member indisponível (com restrição)
    try:
        restricted_date = date.today() + timedelta(days=1)
        date_str = restricted_date.strftime("%d/%m/%Y")
        
        DisponibilidadeService.create_restriction(
            member_id=member_id,
            date_str=date_str,
            description="Indisponível",
        )
        
        is_available = DisponibilidadeService.is_member_available_on_date(
            member_id=member_id,
            check_date=restricted_date,
        )
        
        assert is_available is False
        
        print("✓ member_not_available_with_restriction")
        tests_passed += 1
    except Exception as e:
        print(f"✗ member_not_available_with_restriction: {e}")
        tests_failed += 1

    # Teste 3: Member disponível em data diferente
    try:
        restricted_date = date.today() + timedelta(days=1)
        check_date = date.today() + timedelta(days=5)
        
        is_available = DisponibilidadeService.is_member_available_on_date(
            member_id=member_id,
            check_date=check_date,
        )
        
        assert is_available is True
        
        print("✓ member_available_on_different_date_than_restriction")
        tests_passed += 1
    except Exception as e:
        print(f"✗ member_available_on_different_date_than_restriction: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def main():
    """Roda todos os testes."""
    total_passed = 0
    total_failed = 0

    p, f = test_create_restriction()
    total_passed += p
    total_failed += f

    p, f = test_remove_restriction()
    total_passed += p
    total_failed += f

    p, f = test_get_restrictions()
    total_passed += p
    total_failed += f

    p, f = test_is_member_available()
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    print("RESUMO - TESTES DO SERVICE")
    print("=" * 60)
    print(f"✓ Testes passaram: {total_passed}")
    print(f"✗ Testes falharam: {total_failed}")
    print(f"Total: {total_passed + total_failed}")

    coverage_percent = int((total_passed / (total_passed + total_failed)) * 100) if (total_passed + total_failed) > 0 else 0
    print(f"Coverage: {coverage_percent}%")

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
