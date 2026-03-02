"""Testes para lógica pura de casais (helpers).

RED-GREEN-REFACTOR: Escreve testes que falham (RED),
depois implementa helpers para passar (GREEN).
"""

import pytest

from helpers.casais import (
    validate_different_spouses,
    couple_key,
    couples_are_same,
)


class TestValidateDifferentSpouses:
    """Validar que cônjuge 1 ≠ cônjuge 2."""

    def test_same_spouse_ids_invalid(self):
        """Dois cônjuges com mesmo ID são inválidos."""
        assert not validate_different_spouses("alice", "alice")

    def test_different_spouse_ids_valid(self):
        """Dois cônjuges com IDs diferentes são válidos."""
        assert validate_different_spouses("alice", "bob")
        assert validate_different_spouses("member1", "member2")

    def test_accepts_string_ids(self):
        """Aceita IDs como strings."""
        assert validate_different_spouses("uuid-1", "uuid-2")


class TestCoupleKey:
    """Gerar chave canônica para comparação de casais.

    Dois casais são iguais se têm os mesmos membros
    independente da ordem (Alice+Bob == Bob+Alice).
    """

    def test_couple_key_same_regardless_of_order(self):
        """key(alice, bob) == key(bob, alice)."""
        key1 = couple_key("alice", "bob")
        key2 = couple_key("bob", "alice")
        assert key1 == key2

    def test_couple_key_different_for_different_couples(self):
        """Casais diferentes geram chaves diferentes."""
        key1 = couple_key("alice", "bob")
        key2 = couple_key("alice", "charlie")
        assert key1 != key2

    def test_couple_key_tuple_sorted(self):
        """Chave é tuple com IDs em ordem alfabética."""
        # Garantir determinismo
        key = couple_key("zebra", "apple")
        assert key == ("apple", "zebra")


class TestCouplesAreSame:
    """Verificar se dois casais representam a mesma relação."""

    def test_same_couple_in_same_order(self):
        """Alice+Bob == Alice+Bob."""
        assert couples_are_same("alice", "bob", "alice", "bob")

    def test_same_couple_in_different_order(self):
        """Alice+Bob == Bob+Alice."""
        assert couples_are_same("alice", "bob", "bob", "alice")

    def test_different_couples_not_same(self):
        """Alice+Bob ≠ Alice+Charlie."""
        assert not couples_are_same("alice", "bob", "alice", "charlie")

    def test_different_couples_not_same_either_way(self):
        """Alice+Charlie ≠ Bob+Alice (nenhuma sobreposição)."""
        assert not couples_are_same("alice", "charlie", "bob", "alice")
