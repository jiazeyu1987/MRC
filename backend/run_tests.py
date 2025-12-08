#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Knowledge Base Test Runner

Comprehensive test runner for knowledge base system.
Follows existing project patterns and provides detailed test execution reporting.
"""

import sys
import os
import unittest
import time
from io import StringIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def run_knowledge_base_tests():
    """Run all knowledge base tests and return results"""

    # Test configuration
    test_suite = unittest.TestSuite()

    # Import all test classes
    from tests.test_knowledge_base import (
        TestKnowledgeBaseModel,
        TestRoleKnowledgeBaseModel,
        TestKnowledgeBaseService,
        TestRAGFlowService,
        TestKnowledgeBaseAPI,
        TestIntegrationScenarios
    )
    from tests.test_knowledge_base_integration import (
        TestKnowledgeBaseDiscoveryIntegration,
        TestKnowledgeBaseConversationIntegration,
        TestKnowledgeBaseRoleIntegration,
        TestKnowledgeBasePerformanceIntegration,
        TestKnowledgeBaseConfigurationValidation,
        TestKnowledgeBaseErrorRecovery
    )

    # Add test classes to suite
    test_classes = [
        TestKnowledgeBaseModel,
        TestRoleKnowledgeBaseModel,
        TestKnowledgeBaseService,
        TestRAGFlowService,
        TestKnowledgeBaseAPI,
        TestIntegrationScenarios,
        TestKnowledgeBaseDiscoveryIntegration,
        TestKnowledgeBaseConversationIntegration,
        TestKnowledgeBaseRoleIntegration,
        TestKnowledgeBasePerformanceIntegration,
        TestKnowledgeBaseConfigurationValidation,
        TestKnowledgeBaseErrorRecovery
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Create custom test runner with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True,
        failfast=False
    )

    # Run tests
    start_time = time.time()
    result = runner.run(test_suite)
    end_time = time.time()

    # Get output
    output = stream.getvalue()

    # Generate summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0

    summary = {
        'total_tests': total_tests,
        'passed': total_tests - failures - errors,
        'failures': failures,
        'errors': errors,
        'skipped': skipped,
        'success_rate': success_rate,
        'duration': end_time - start_time,
        'output': output,
        'successful': failures == 0 and errors == 0
    }

    # Print summary
    print("\n" + "="*80)
    print("KNOWLEDGE BASE TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Duration: {summary['duration']:.2f} seconds")

    if failures > 0:
        print(f"\nFAILURES ({failures}):")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if errors > 0:
        print(f"\nERRORS ({errors}):")
        for test, traceback in result.errors:
            print(f"  - {test}")

    print("\n" + "="*80)

    return summary

def run_specific_test(test_name=None):
    """Run a specific test class or method"""

    if not test_name:
        print("Please specify a test name (e.g., 'TestKnowledgeBaseModel' or 'TestKnowledgeBaseModel.test_knowledge_base_creation')")
        return False

    # Try to load the specific test
    try:
        from tests.test_knowledge_base import TestKnowledgeBaseModel, TestRoleKnowledgeBaseModel, TestKnowledgeBaseService, TestRAGFlowService, TestKnowledgeBaseAPI, TestIntegrationScenarios
        from tests.test_knowledge_base_integration import (
            TestKnowledgeBaseDiscoveryIntegration,
            TestKnowledgeBaseConversationIntegration,
            TestKnowledgeBaseRoleIntegration,
            TestKnowledgeBasePerformanceIntegration,
            TestKnowledgeBaseConfigurationValidation,
            TestKnowledgeBaseErrorRecovery
        )

        # Map test names to classes
        test_classes = {
            'TestKnowledgeBaseModel': TestKnowledgeBaseModel,
            'TestRoleKnowledgeBaseModel': TestRoleKnowledgeBaseModel,
            'TestKnowledgeBaseService': TestKnowledgeBaseService,
            'TestRAGFlowService': TestRAGFlowService,
            'TestKnowledgeBaseAPI': TestKnowledgeBaseAPI,
            'TestIntegrationScenarios': TestIntegrationScenarios,
            'TestKnowledgeBaseDiscoveryIntegration': TestKnowledgeBaseDiscoveryIntegration,
            'TestKnowledgeBaseConversationIntegration': TestKnowledgeBaseConversationIntegration,
            'TestKnowledgeBaseRoleIntegration': TestKnowledgeBaseRoleIntegration,
            'TestKnowledgeBasePerformanceIntegration': TestKnowledgeBasePerformanceIntegration,
            'TestKnowledgeBaseConfigurationValidation': TestKnowledgeBaseConfigurationValidation,
            'TestKnowledgeBaseErrorRecovery': TestKnowledgeBaseErrorRecovery
        }

        # Check if it's a class name
        if test_name in test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_name])
        else:
            # Try to load as a specific test method
            suite = unittest.TestSuite()
            parts = test_name.split('.')

            if len(parts) == 2 and parts[0] in test_classes:
                test_class = test_classes[parts[0]]
                if hasattr(test_class, parts[1]):
                    suite.addTest(test_class(parts[1]))
                else:
                    print(f"Test method '{parts[1]}' not found in class '{parts[0]}'")
                    return False
            else:
                print(f"Test '{test_name}' not found")
                return False

        # Run the test
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"Error running test: {e}")
        return False

def main():
    """Main test runner function"""
    import argparse

    parser = argparse.ArgumentParser(description='Knowledge Base Test Runner')
    parser.add_argument('--test', '-t', help='Run specific test class or method')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick test run (skip integration tests)')

    args = parser.parse_args()

    print("Knowledge Base Test Runner")
    print("="*50)

    if args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    elif args.quick:
        # Run only unit tests (skip integration tests)
        from tests.test_knowledge_base import TestKnowledgeBaseModel, TestRoleKnowledgeBaseModel, TestKnowledgeBaseService, TestRAGFlowService, TestKnowledgeBaseAPI

        test_classes = [
            TestKnowledgeBaseModel,
            TestRoleKnowledgeBaseModel,
            TestKnowledgeBaseService,
            TestRAGFlowService,
            TestKnowledgeBaseAPI
        ]

        suite = unittest.TestSuite()
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)

        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        # Run all tests
        summary = run_knowledge_base_tests()

        if summary['successful']:
            print("\n✅ ALL TESTS PASSED! Knowledge base system is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED! Please review the errors above.")
            sys.exit(1)

if __name__ == '__main__':
    main()