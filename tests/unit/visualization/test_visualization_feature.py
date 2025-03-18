#!/usr/bin/env python3
"""
Test script for the PDF field visualization feature.
This script performs a series of tests to ensure that the visualization features work correctly.
"""

import os
import json
import sys
import shutil
import logging
import unittest
from datetime import datetime

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Now we can import from tests
from tests.test_config import TEST_TEMPLATES_DIR, TEST_PDFS_DIR, get_test_template_path, get_test_pdf_path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get BASE_DIR
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))

class TestVisualizationFeature(unittest.TestCase):
    """Test case for visualization feature."""
    
    def setUp(self):
        """Set up test environment."""
        self.check_directories()
    
    def check_directories(self):
        """Check if required directories exist."""
        required_dirs = [
            TEST_TEMPLATES_DIR,
            TEST_PDFS_DIR,
            os.path.join(BASE_DIR, "static/images"),
            os.path.join(BASE_DIR, "static/visualizations")
        ]
        
        missing_dirs = []
        for directory in required_dirs:
            if not os.path.exists(directory):
                missing_dirs.append(directory)
        
        if missing_dirs:
            logger.error(f"Missing directories: {', '.join(missing_dirs)}")
            logger.info("Creating missing directories...")
            for directory in missing_dirs:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
    
    def test_template_exists(self):
        """Test if template exists and is valid."""
        template_path = get_test_template_path("test_visualization_template.json")
        self.assertTrue(os.path.exists(template_path), f"Test template not found: {template_path}")
        
        # Check if template is valid JSON
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
            self.assertIsInstance(template, dict)
            self.assertIn('fields', template)
        except json.JSONDecodeError:
            self.fail(f"Template file is not valid JSON: {template_path}")
    
    def test_pdf_exists(self):
        """Test if test PDF exists."""
        pdf_path = get_test_pdf_path("test_visualization_form.pdf")
        self.assertTrue(os.path.exists(pdf_path), f"Test PDF not found: {pdf_path}")
    
    def test_placeholder_images(self):
        """Test if placeholder images exist."""
        placeholder_dir = os.path.join(BASE_DIR, "static/images")
        required_placeholders = [
            "loading-placeholder.png",
            "error-placeholder.png"
        ]
        
        for placeholder in required_placeholders:
            placeholder_path = os.path.join(placeholder_dir, placeholder)
            self.assertTrue(os.path.exists(placeholder_path), f"Placeholder image not found: {placeholder_path}")
    
    def test_create_visualization(self):
        """Test creating a visualization."""
        # This is a placeholder for a real test that would create a visualization
        # In a real test, we would call the visualization function and check the result
        # For now, just pass
        pass

# For backward compatibility with direct script execution
def check_directories():
    test = TestVisualizationFeature()
    test.check_directories()

def check_template():
    test = TestVisualizationFeature()
    test.test_template_exists()

def check_test_pdf():
    test = TestVisualizationFeature()
    test.test_pdf_exists()

def check_placeholder_images():
    test = TestVisualizationFeature()
    test.test_placeholder_images()

def create_test_visualization():
    test = TestVisualizationFeature()
    test.test_create_visualization()

def main():
    """Run visualization feature tests."""
    # Set up test environment
    check_directories()
    
    # Run tests
    unittest.main()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 