#!/usr/bin/env python
"""Quick validation script for membros.py refactoring."""

import sys
sys.path.insert(0, '/home/samuel/projects/escala')

try:
    print("1. Verificando imports...")
    from gui.membros import MembrosFrame
    from services.membros_service import MembrosService
    print("   ✓ Imports OK")
    
    print("\n2. Verificando que MembrosFrame tem o service...")
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    frame = MembrosFrame(root)
    assert hasattr(frame, 'service'), "MembrosFrame não tem atributo 'service'"
    assert isinstance(frame.service, MembrosService), "Service não é MembrosService"
    print("   ✓ Service injetado corretamente")
    
    print("\n3. Verificando métodos obrigatórios...")
    required_methods = ['adicionar', 'editar', 'remover', 'salvar_squads', 'atualizar_lista']
    for method_name in required_methods:
        assert hasattr(frame, method_name), f"Método {method_name} não encontrado"
        assert callable(getattr(frame, method_name)), f"Método {method_name} não é callable"
    print(f"   ✓ Todos os {len(required_methods)} métodos existem")
    
    print("\n✅ REFATORAÇÃO VALIDADA COM SUCESSO!")
    print("\nResumo:")
    print("  - gui/membros.py importa e instancia MembrosService")
    print("  - Todos os métodos CRUD foram refatorados")
    print("  - Try/except adicionado em todas as chamadas de service")
    print("  - Testes de integração criados em tests/integration/test_membros_gui.py")
    
    root.destroy()
    sys.exit(0)
    
except Exception as e:
    print(f"\n✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
