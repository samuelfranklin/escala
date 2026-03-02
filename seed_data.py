#!/usr/bin/env python3
# seed_data.py - Script para popular banco com dados de teste

import sys

from infra.database import (
    Base,
    Member,
    Squad,
    MemberSquad,
    Event,
    EventSquad,
    FamilyCouple,
    create_tables,
    session_scope,
    engine,
)


def seed_database() -> None:
    """Popula o banco com dados de teste realistas."""
    print("🌱 Iniciando seed de dados...")

    # DROP + CREATE tabelas (force clean start)
    print("Limpando banco... (drop + create)")
    Base.metadata.drop_all(engine)
    create_tables()
    print("✓ Tabelas criadas (clean)")

    with session_scope() as session:
        # ── MEMBROS ──
        membros = [
            Member(name="João Silva", phone_number="11999001234", email="joao@email.com", instagram="@joao", status=True),
            Member(name="Maria Santos", phone_number="11999005678", email="maria@email.com", instagram="@maria", status=True),
            Member(name="Pedro Oliveira", phone_number="11999009012", email="pedro@email.com", instagram="@pedro", status=True),
            Member(name="Ana Costa", phone_number="11999003456", email="ana@email.com", instagram="@ana", status=True),
            Member(name="Carlos Mendes", phone_number="11999007890", email="carlos@email.com", instagram="@carlos", status=True),
            Member(name="Lucia Ferreira", phone_number="11999002345", email="lucia@email.com", instagram="@lucia", status=True),
            Member(name="Roberto Alves", phone_number="11999006789", email="roberto@email.com", instagram="@roberto", status=True),
            Member(name="Patricia Lima", phone_number="11999001111", email="patricia@email.com", instagram="@patricia", status=True),
        ]
        session.add_all(membros)
        session.flush()
        print(f"✓ {len(membros)} membros adicionados")

        # ── SQUADS (TIMES) ──
        squads = [
            Squad(nome="Líderes"),
            Squad(nome="Segurança"),
            Squad(nome="Publicidade"),
            Squad(nome="Louvor"),
        ]
        session.add_all(squads)
        session.flush()
        print(f"✓ {len(squads)} times adicionados")

        # ── ASSOCIAÇÕES MEMBRO-SQUAD ──
        associations = [
            # João -> Líderes (Líder)
            MemberSquad(member_id=membros[0].id, squad_id=squads[0].id, level=4),
            # Maria -> Segurança (Treinador)
            MemberSquad(member_id=membros[1].id, squad_id=squads[1].id, level=3),
            # Pedro -> Publicidade (Membro)
            MemberSquad(member_id=membros[2].id, squad_id=squads[2].id, level=2),
            # Ana -> Louvor (Membro)
            MemberSquad(member_id=membros[3].id, squad_id=squads[3].id, level=2),
            # Carlos -> Líderes (Membro)
            MemberSquad(member_id=membros[4].id, squad_id=squads[0].id, level=2),
            # Lucia -> Segurança (Recruta)
            MemberSquad(member_id=membros[5].id, squad_id=squads[1].id, level=1),
            # Roberto -> Louvor (Treinador)
            MemberSquad(member_id=membros[6].id, squad_id=squads[3].id, level=3),
            # Patricia -> Publicidade (Recruta)
            MemberSquad(member_id=membros[7].id, squad_id=squads[2].id, level=1),
        ]
        session.add_all(associations)
        session.flush()
        print(f"✓ {len(associations)} associações membro-squad adicionadas")

        # ── CASAIS ──
        casais = [
            FamilyCouple(member1_id=membros[0].id, member2_id=membros[1].id, family_type=1),  # João + Maria
            FamilyCouple(member1_id=membros[2].id, member2_id=membros[3].id, family_type=1),  # Pedro + Ana
        ]
        session.add_all(casais)
        session.flush()
        print(f"✓ {len(casais)} casais adicionados")

        # ── EVENTOS ──
        events = [
            Event(name="Culto Segunda", type="fixo", day_of_week="Segunda", time="19:00", details="Culto semanal"),
            Event(name="Culto Quinta", type="fixo", day_of_week="Quinta", time="19:00", details="Culto semanal"),
            Event(name="Culto Domingo", type="fixo", day_of_week="Domingo", time="10:00", details="Culto principal"),
            Event(name="Conferência Anual", type="sazonal", date="2026-08-15", time="09:00", details="Evento especial anual"),
            Event(name="Retiro", type="eventual", date="2026-04-10", time="08:00", details="Retiro espiritual"),
        ]
        session.add_all(events)
        session.flush()
        print(f"✓ {len(events)} eventos adicionados")

        # ── CONFIGURAÇÕES DE EVENTO-SQUAD ──
        event_configs = [
            # Culto Segunda: 2 de cada squad
            EventSquad(event_id=events[0].id, squad_id=squads[0].id, quantity=2, level=3),
            EventSquad(event_id=events[0].id, squad_id=squads[1].id, quantity=2, level=3),
            EventSquad(event_id=events[0].id, squad_id=squads[2].id, quantity=1, level=2),
            EventSquad(event_id=events[0].id, squad_id=squads[3].id, quantity=2, level=3),
            # Culto Quinta: similar
            EventSquad(event_id=events[1].id, squad_id=squads[0].id, quantity=2, level=3),
            EventSquad(event_id=events[1].id, squad_id=squads[1].id, quantity=2, level=3),
            EventSquad(event_id=events[1].id, squad_id=squads[2].id, quantity=1, level=2),
            EventSquad(event_id=events[1].id, squad_id=squads[3].id, quantity=2, level=3),
            # Culto Domingo: mais pessoas
            EventSquad(event_id=events[2].id, squad_id=squads[0].id, quantity=3, level=3),
            EventSquad(event_id=events[2].id, squad_id=squads[1].id, quantity=3, level=3),
            EventSquad(event_id=events[2].id, squad_id=squads[2].id, quantity=2, level=2),
            EventSquad(event_id=events[2].id, squad_id=squads[3].id, quantity=4, level=3),
        ]
        session.add_all(event_configs)
        session.flush()
        print(f"✓ {len(event_configs)} configurações evento-squad adicionadas")

        # ── COMMIT ──
        session.commit()
        print("\n✅ Seed concluído com sucesso!")
        print(f"\n📊 Resumo:")
        print(f"   - {len(membros)} membros")
        print(f"   - {len(squads)} times")
        print(f"   - {len(associations)} associações membro-squad")
        print(f"   - {len(casais)} casais")
        print(f"   - {len(events)} eventos")
        print(f"   - {len(event_configs)} configurações evento-squad")


if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
