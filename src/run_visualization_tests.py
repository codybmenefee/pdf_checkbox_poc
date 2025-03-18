#!/usr/bin/env python3
"""
Script to run all visualization-related tests.
"""

import os
import sys
import unittest
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all visualization tests."""
    logger.info("Starting visualization tests...")
    
    # Collect tests from test modules
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    try:
        from src.test_visualization import TestVisualization
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualization))
        logger.info("Added visualization unit tests")
    except ImportError as e:
        logger.error(f"Error importing visualization unit tests: {str(e)}")
    
    # Add API tests
    try:
        from src.test_visualization_api import TestVisualizationAPI
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualizationAPI))
        logger.info("Added visualization API tests")
    except ImportError as e:
        logger.error(f"Error importing visualization API tests: {str(e)}")
    
    # Add end-to-end tests
    try:
        from src.test_e2e_checkbox_visualization import TestCheckboxVisualizationE2E
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestCheckboxVisualizationE2E))
        logger.info("Added visualization end-to-end tests")
    except ImportError as e:
        logger.error(f"Error importing visualization end-to-end tests: {str(e)}")
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Display summary
    logger.info("Visualization tests completed")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Return test result
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 