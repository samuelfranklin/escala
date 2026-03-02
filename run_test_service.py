#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from tests.services.test_eventos_service import TestEventosService, TestEventosServiceIntegration

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEventosService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEventosServiceIntegration))

    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    print(f'\n{"="*70}')
    print(f'Total: {result.testsRun} tests')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    print(f'Result: {"✅ PASSED" if result.wasSuccessful() else "❌ FAILED"}')
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)
