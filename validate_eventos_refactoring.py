#!/usr/bin/env python3
"""
Validação da refatoração de gui/eventos_orm.py
"""

import sys
import os
import tempfile

# Setup temp DB
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
temp_db.close()
os.environ['DATABASE_URL'] = f'sqlite:///{temp_db.name}'

sys.path.insert(0, '/home/samuel/projects/escala')

try:
    print("=" * 70)
    print("VALIDAÇÃO: gui/eventos_orm.py refatorado com EventosService")
    print("=" * 70)
    print()
    
    # 1. Verificar imports e estrutura
    print("1. Verificando imports...")
    from gui.eventos_orm import EventosFrame
    from services.eventos_service import EventosService
    from infra.database import create_tables, session_scope, Event, Squad, EventSquad
    print("   ✓ Todos os imports OK")
    print()
    
    # 2. Check framework
    import tkinter as tk
    print("2. Criando janela Tkinter...")
    root = tk.Tk()
    root.withdraw()
    print("   ✓ Janela criada")
    print()
    
    # 3. Setup DB
    print("3. Inicializando banco de dados...")
    create_tables()
    
    # Criar squads
    with session_scope() as session:
        session.query(EventSquad).delete()
        session.query(Event).delete()
        session.query(Squad).delete()
        session.commit()
        
        squads = [
            Squad(id="sq-1", nome="Squad A"),
            Squad(id="sq-2", nome="Squad B"),
        ]
        session.add_all(squads)
        session.commit()
    print("   ✓ Banco pronto com squads")
    print()
    
    # 4. Teste refatoração
    print("4. Testando refatoração...")
    frame = EventosFrame(root)
    frame.pack()
    
    # Verificar service
    assert hasattr(frame, 'service'), "Frame não tem 'service'"
    assert isinstance(frame.service, EventosService), "Service não é EventosService"
    print("   ✓ EventosService injetado corretamente")
    
    # Verificar métodos
    assert hasattr(frame, 'adicionar'), "Falta método 'adicionar'"
    assert hasattr(frame, 'editar'), "Falta método 'editar'"
    assert hasattr(frame, 'remover'), "Falta método 'remover'"
    assert hasattr(frame, 'atualizar_lista'), "Falta método 'atualizar_lista'"
    print("   ✓ Todos os métodos CRUD presentes")
    print()
    
    # 5. Teste criação de evento
    print("5. Testando criação de evento via service...")
    success, message, event = frame.service.create_event(
        name="Culto",
        event_type="fixo",
        time="19:00",
        day_of_week="Domingo",
        date=None,
        details="Culto semanal"
    )
    
    assert success, f"Falha ao criar evento: {message}"
    assert event is not None, "Event retornou None"
    assert event.name == "Culto", f"Nome esperado 'Culto', got '{event.name}'"
    print(f"   ✓ Evento criado: '{event.name}' (ID: {event.id})")
    print()
    
    # 6. Teste listagem
    print("6. Testando listagem de eventos...")
    eventos = frame.service.list_all_events()
    assert len(eventos) >= 1, "Nenhum evento listado"
    print(f"   ✓ {len(eventos)} evento(s) listado(s)")
    print()
    
    # 7. Teste atualização
    print("7. Testando atualização de evento...")
    success, message, updated = frame.service.update_event(
        event_id=event.id,
        name="Culto Atualizado"
    )
    
    assert success, f"Falha ao atualizar: {message}"
    assert updated.name == "Culto Atualizado", f"Nome não atualizado"
    print(f"   ✓ Evento atualizado: '{updated.name}'")
    print()
    
    # 8. Teste configuração de squads
    print("8. Testando configuração de squads...")
    success, message = frame.service.configure_event_squads(
        event_id=event.id,
        squad_quantities={"sq-1": 2, "sq-2": 1}
    )
    
    assert success, f"Falha ao configurar squads: {message}"
    
    # Verificar no BD
    with session_scope() as session:
        event_squads = session.query(EventSquad).filter(
            EventSquad.event_id == event.id
        ).all()
        assert len(event_squads) == 2, f"Esperava 2 squads, got {len(event_squads)}"
    
    print(f"   ✓ {len(event_squads)} squad(s) configurado(s)")
    print()
    
    # 9. Teste deleção
    print("9. Testando deleção de evento...")
    event_id = event.id
    success, message = frame.service.delete_event(event_id)
    
    assert success, f"Falha ao deletar: {message}"
    
    # Verificar no BD
    with session_scope() as session:
        deleted = session.query(Event).filter(Event.id == event_id).first()
        assert deleted is None, "Evento não foi deletado"
    
    print(f"   ✓ Evento deletado com sucesso")
    print()
    
    # Cleanup
    frame.destroy()
    root.destroy()
    
    print("=" * 70)
    print("✓ VALIDAÇÃO COMPLETA - TUDO OK!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except:
        pass
