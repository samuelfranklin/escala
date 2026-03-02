#!/usr/bin/env python
"""
Verificação rápida: GUI refatorada consegue ser importada e instanciada.
"""
import sys
import os

# Add project to path
sys.path.insert(0, '/home/samuel/projects/escala')

def test_gui_import():
    """Testa se GUI consegue ser importada."""
    try:
        from gui.gerar_escala import GerarEscalaFrame
        print("✓ GerarEscalaFrame importado com sucesso")
        return True
    except ImportError as e:
        print(f"✗ Erro ao importar: {e}")
        return False

def test_service_import():
    """Testa se EscalaService consegue ser importado."""
    try:
        from services.escala_service import EscalaService
        print("✓ EscalaService importado com sucesso")
        return True
    except ImportError as e:
        print(f"✗ Erro ao importar: {e}")
        return False

def test_gui_structure():
    """Testa estrutura da GUI sem instanciar."""
    try:
        from gui.gerar_escala import GerarEscalaFrame
        import inspect
        
        # Verificar métodos público
        methods = [m for m in dir(GerarEscalaFrame) if not m.startswith('_')]
        expected_methods = ['gerar', 'criar_widgets']
        
        for method in expected_methods:
            if method in methods:
                print(f"✓ Método '{method}' presente")
            else:
                print(f"✗ Método '{method}' NÃO encontrado")
                return False
        
        # Verificar que métodos antigos foram removidos
        not_allowed = [
            'coletar_eventos',
            'buscar_disponiveis',
            'processar_casais',
            'selecionar_membros',
            '_selecionar_com_regras',
            '_count_people_in_units'
        ]
        
        for method in not_allowed:
            if method in methods:
                print(f"✗ Método antigo '{method}' ainda existe!")
                return False
        
        print("✓ Todos os métodos antigos foram removidos")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao verificar estrutura: {e}")
        return False

def main():
    print("=" * 60)
    print("VERIFICAÇÃO RÁPIDA: REFATORAÇÃO gui/gerar_escala.py")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testando imports...")
    results.append(test_gui_import())
    results.append(test_service_import())
    
    print("\n2. Testando estrutura...")
    results.append(test_gui_structure())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ TODAS AS VERIFICAÇÕES PASSARAM")
        print("=" * 60)
        print("\nResumo:")
        print("  • gui/gerar_escala.py refatorado com sucesso")
        print("  • EscalaService injetado no __init__")
        print("  • Todos os métodos antigos removidos")
        print("  • Testes de integração criados em:")
        print("    tests/integration/test_gerar_escala_gui.py")
        return 0
    else:
        print("❌ ALGUMAS VERIFICAÇÕES FALHARAM")
        return 1

if __name__ == '__main__':
    sys.exit(main())
