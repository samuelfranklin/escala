"""Testes de integração para o service de casais.

Testa a orquestra entre BD (session_scope) e helpers.
Valida validações de negócio e persistência.
"""

import pytest

from services.casais_service import (
    create_couple,
    delete_couple,
    find_couple,
    member_has_couple,
    get_all_couples,
)


class TestCreateCouple:
    """Teste criar casal."""

    def test_create_couple_success(self, members_fixture):
        """Criar casal com IDs válidos e diferentes."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        couple = create_couple(alice_id, bob_id)
        
        assert couple is not None
        assert {couple.member1_id, couple.member2_id} == {alice_id, bob_id}

    def test_create_couple_same_person_fails(self, members_fixture):
        """Criar casal com mesma pessoa em ambos os lados falha."""
        alice_id = members_fixture["Alice"]
        
        with pytest.raises(ValueError, match="diferentes"):
            create_couple(alice_id, alice_id)

    def test_create_couple_duplicate_fails(self, members_fixture):
        """Criar casal duplicado falha."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        # Criar primeiro casal
        create_couple(alice_id, bob_id)
        
        # Tentar criar mesmo casal novamente
        with pytest.raises(ValueError, match="já existe"):
            create_couple(alice_id, bob_id)

    def test_create_couple_reverse_order_is_duplicate(self, members_fixture):
        """Criar casal ao inverso também constitu duplicata."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        # Criar Alice + Bob
        create_couple(alice_id, bob_id)
        
        # Tentar criar Bob + Alice (mesmo casal, ordem inversa)
        with pytest.raises(ValueError, match="já existe"):
            create_couple(bob_id, alice_id)


class TestFindCouple:
    """Teste encontrar casal."""

    def test_find_couple_exists(self, members_fixture):
        """Encontrar casal que existe."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        created = create_couple(alice_id, bob_id)
        found = find_couple(alice_id, bob_id)
        
        assert found is not None
        assert found.id == created.id

    def test_find_couple_reverse_order(self, members_fixture):
        """Encontrar casal mesmo em ordem inversa."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        created = create_couple(alice_id, bob_id)
        found = find_couple(bob_id, alice_id)
        
        assert found is not None
        assert found.id == created.id

    def test_find_couple_not_exists(self, members_fixture):
        """Encontrar casal que não existe retorna None."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        found = find_couple(alice_id, bob_id)
        assert found is None


class TestMemberHasCouple:
    """Teste se membro já está em um casal."""

    def test_member_has_couple_true(self, members_fixture):
        """Membro em casal retorna True."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        create_couple(alice_id, bob_id)
        
        assert member_has_couple(alice_id)
        assert member_has_couple(bob_id)

    def test_member_has_couple_false(self, members_fixture):
        """Membro sem casal retorna False."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        charlie_id = members_fixture["Charlie"]
        
        create_couple(alice_id, bob_id)
        
        assert not member_has_couple(charlie_id)


class TestDeleteCouple:
    """Teste deletar casal."""

    def test_delete_couple_success(self, members_fixture):
        """Deletar casal com sucesso."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        
        couple = create_couple(alice_id, bob_id)
        delete_couple(couple.id)
        
        found = find_couple(alice_id, bob_id)
        assert found is None

    def test_delete_couple_invalid_id(self, members_fixture):
        """Deletar casal inexistente não lança erro."""
        # Não deve lançar erro
        delete_couple("invalid-id")


class TestGetAllCouples:
    """Teste listar todos os casais."""

    def test_get_all_couples_empty(self, members_fixture):
        """Listar casais quando vazio retorna lista vazia."""
        all_couples = get_all_couples()
        assert all_couples == []

    def test_get_all_couples_multiple(self, members_fixture):
        """Listar múltiplos casais."""
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        charlie_id = members_fixture["Charlie"]
        dave_id = members_fixture["Dave"]
        eve_id = members_fixture["Eve"]
        frank_id = members_fixture["Frank"]
        
        couple1 = create_couple(alice_id, bob_id)
        couple2 = create_couple(charlie_id, dave_id)
        couple3 = create_couple(eve_id, frank_id)
        
        all_couples = get_all_couples()
        assert len(all_couples) == 3
        assert couple1.id in [c.id for c in all_couples]
        assert couple2.id in [c.id for c in all_couples]
        assert couple3.id in [c.id for c in all_couples]
