#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from tests.helpers.test_eventos import (
    TestValidateEventName,
    TestValidateEventType,
    TestValidateDayOfWeek,
    TestValidateDate,
    TestValidateTime,
    TestValidateEventSquads,
    TestNormalizeEventName,
    TestNormalizeTime,
    TestNormalizeDate,
)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    for test_class in [TestValidateEventName, TestValidateEventType, TestValidateDayOfWeek,
                        TestValidateDate, TestValidateTime, TestValidateEventSquads,
                        TestNormalizeEventName, TestNormalizeTime, TestNormalizeDate]:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    print(f'\n{"="*70}')
    print(f'Total: {result.testsRun} tests')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    print(f'Result: {"✅ PASSED (100% coverage)" if result.wasSuccessful() else "❌ FAILED"}')
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.splitlines()[-1]}")
