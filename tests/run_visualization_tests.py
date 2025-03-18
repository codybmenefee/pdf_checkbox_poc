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

# Add the current directory to the path to fix imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import path setup
from path_setup import BASE_DIR

def run_tests():
    """Run all visualization tests."""
    logger.info("Starting visualization tests...")
    
    # Collect tests from test modules
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add consolidated core tests
    try:
        from unit.visualization.test_visualization_core import TestVisualizationCore
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualizationCore))
        logger.info("Added visualization core tests")
    except ImportError as e:
        logger.error(f"Error importing visualization core tests: {str(e)}")
    
    # Add consolidated API tests
    try:
        from unit.visualization.test_visualization_api import TestVisualizationAPI
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualizationAPI))
        logger.info("Added visualization API tests")
    except ImportError as e:
        logger.error(f"Error importing visualization API tests: {str(e)}")
    
    # Add consolidated UI tests
    try:
        from unit.visualization.test_visualization_ui import TestFieldVisualizationUI, TestCheckboxVisualizationUI, TestVisualizationAssets
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestFieldVisualizationUI))
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestCheckboxVisualizationUI))
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualizationAssets))
        logger.info("Added visualization UI tests")
    except ImportError as e:
        logger.error(f"Error importing visualization UI tests: {str(e)}")
    
    # Add consolidated E2E tests
    try:
        from unit.visualization.test_visualization_e2e import TestCheckboxVisualizationE2E, TestFieldVisualizationE2E
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestCheckboxVisualizationE2E))
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestFieldVisualizationE2E))
        logger.info("Added visualization E2E tests")
    except ImportError as e:
        logger.error(f"Error importing visualization E2E tests: {str(e)}")
    
    # For backward compatibility, add legacy visualization tests if they exist
    try:
        from unit.visualization.test_visualization_feature import TestVisualizationFeature
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualizationFeature))
        logger.info("Added legacy visualization feature tests")
    except ImportError as e:
        logger.error(f"Error importing legacy visualization feature tests: {str(e)}")
    
    try:
        from unit.test_visualization import TestVisualization
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualization))
        logger.info("Added legacy visualization unit tests")
    except ImportError as e:
        logger.error(f"Error importing legacy visualization unit tests: {str(e)}")
    
    try:
        from unit.test_visualization_api import TestVisualizationAPI
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestVisualizationAPI))
        logger.info("Added legacy visualization API tests")
    except ImportError as e:
        logger.error(f"Error importing legacy visualization API tests: {str(e)}")
    
    try:
        from unit.test_field_overlay import TestFieldOverlay
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestFieldOverlay))
        logger.info("Added legacy field overlay tests")
    except ImportError as e:
        logger.error(f"Error importing legacy field overlay tests: {str(e)}")
    
    try:
        from unit.test_e2e_field_visualization import TestE2EFieldVisualization
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestE2EFieldVisualization))
        logger.info("Added legacy E2E field visualization tests")
    except ImportError as e:
        logger.error(f"Error importing legacy E2E field visualization tests: {str(e)}")
    
    try:
        from unit.test_e2e_checkbox_visualization import TestE2ECheckboxVisualization
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestE2ECheckboxVisualization))
        logger.info("Added legacy E2E checkbox visualization tests")
    except ImportError as e:
        logger.error(f"Error importing legacy E2E checkbox visualization tests: {str(e)}")
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    logger.info("Visualization tests completed.")
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 