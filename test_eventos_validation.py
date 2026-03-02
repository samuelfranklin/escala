#!/usr/bin/env python3
"""Validar estrutura do test_eventos_gui.py e executar testes."""

import sys
import os
import ast

# Listar testes
test_file = '/home/samuel/projects/escala/tests/integration/test_eventos_gui.py'

with open(test_file, 'r') as f:
    content = f.read()
    tree = ast.parse(content)

print("=" * 60)
print("TEST CLASSES AND METHODS IN test_eventos_gui.py")
print("=" * 60)

test_counts = {}
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        test_counts[node.name] = 0
        print(f"\n{node.name}:")
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                test_counts[node.name] += 1
                print(f"  ✓ {item.name}")

total = sum(test_counts.values())
print(f"\n{'=' * 60}")
print(f"SUMMARY: {len(test_counts)} test classes, {total} test methods")
print(f"{'=' * 60}\n")

# Echo the structure
for cls, count in test_counts.items():
    print(f"  - {cls}: {count} tests")
