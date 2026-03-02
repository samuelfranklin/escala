#!/usr/bin/env python3
"""
Script para executar testes de integração e capturar cobertura.
"""

import subprocess
import sys
import os

os.chdir('/home/samuel/projects/escala')

# Executar testes com cobertura
cmd = [
    sys.executable, '-m', 'pytest',
    'tests/integration/test_eventos_gui.py',
    '--cov=gui.eventos_orm',
    '--cov=services.eventos_service',
    '--cov-report=term-missing',
    '-v',
    '--tb=short'
]

print("=" * 70)
print("EXECUTANDO TESTES DE INTEGRAÇÃO - EVENTOS_GUI")
print("=" * 70)
print()

result = subprocess.run(cmd, capture_output=False, text=True)
sys.exit(result.returncode)
