#!/usr/bin/env python3
"""
Test runner script for all project tests.
"""

import unittest
import sys
import os

if __name__ == "__main__":
    # Set current directory to the script's directory for proper imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Load test modules
    test_modules_added = []
    
    # Discover and run all tests in the current directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('.', pattern='test_*.py')
    test_modules_added.append("main directory tests")
    
    # Add the new Document AI tests
    document_ai_tests = [
        'document_ai.test_document_ai_core',
        'document_ai.test_document_ai_models',
        'document_ai.test_document_ai_utils'
    ]
    
    for test_module in document_ai_tests:
        try:
            module = __import__(test_module, fromlist=[''])
            test_suite.addTest(unittest.TestLoader().loadTestsFromModule(module))
            test_modules_added.append(test_module)
        except ImportError as e:
            print(f"Warning: Could not import {test_module}: {e}")
    
    # Add the visualization tests
    visualization_tests = [
        'test_visualization',
        'test_visualization_api',
        'test_e2e_checkbox_visualization'
    ]
    
    for test_module in visualization_tests:
        try:
            module = __import__(test_module, fromlist=[''])
            test_suite.addTest(unittest.TestLoader().loadTestsFromModule(module))
            test_modules_added.append(test_module)
        except ImportError as e:
            print(f"Warning: Could not import {test_module}: {e}")
    
    # Add the static file handling tests
    try:
        static_file_module = __import__("test_static_file_handling")
        test_suite.addTest(unittest.TestLoader().loadTestsFromModule(static_file_module))
        test_modules_added.append("test_static_file_handling.py")
    except ImportError as e:
        print(f"Warning: Could not import static file handling tests: {e}")
    
    # Add the original tests.py module
    try:
        tests_module = __import__("tests")
        test_suite.addTest(unittest.TestLoader().loadTestsFromModule(tests_module))
        test_modules_added.append("tests.py")
    except ImportError as e:
        print(f"Warning: Could not import tests.py module: {e}")
    
    # Run the tests
    print(f"Running tests from: {', '.join(test_modules_added)}")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Set exit code based on test results
    sys.exit(not result.wasSuccessful()) 