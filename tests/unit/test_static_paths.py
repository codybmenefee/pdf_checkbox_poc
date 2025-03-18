#!/usr/bin/env python3
"""
Test script to verify static file path configuration.
This script verifies that the static file path configuration in app.py is working correctly.
"""

import os
import sys
import json
import requests
import logging
import pytest
from pprint import pprint
from datetime import datetime

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Now we can import from tests
from tests.test_config import TEST_TEMPLATES_DIR, TEST_PDFS_DIR, get_test_resource_path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if Flask app is running
def check_flask_app():
    try:
        response = requests.get('http://localhost:5004/api/health')
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        logger.error("Flask app is not running. Please start it with 'python app.py'.")
        return False

def test_static_file_access():
    """Test if static files can be accessed."""
    if not check_flask_app():
        pytest.skip("Flask app is not running. Skipping test.")

    # Test static files
    static_files = [
        '/static/css/main.css',
        '/static/js/main.js',
        '/static/images/placeholder.png'
    ]

    for file_path in static_files:
        logger.info(f"Testing static file: {file_path}")
        response = requests.get(f'http://localhost:5004{file_path}')
        
        if response.status_code == 200:
            logger.info(f"✅ Static file accessible: {file_path}")
        else:
            logger.error(f"❌ Failed to access static file: {file_path}")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Response text: {response.text[:100]}...")
    
    logger.info("Static file access test completed.")

def test_visualization_access():
    """Test if visualization files can be accessed."""
    if not check_flask_app():
        pytest.skip("Flask app is not running. Skipping test.")

    # Find visualization files
    visualization_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static/visualizations')
    if not os.path.exists(visualization_dir):
        logger.error(f"Visualization directory not found: {visualization_dir}")
        return
    
    # Test first 3 visualization files
    visualization_files = [f for f in os.listdir(visualization_dir) if f.endswith('.html')][:3]
    
    if not visualization_files:
        logger.warning("No visualization files found to test.")
        return
    
    for file_name in visualization_files:
        file_path = f'/static/visualizations/{file_name}'
        logger.info(f"Testing visualization file: {file_path}")
        response = requests.get(f'http://localhost:5004{file_path}')
        
        if response.status_code == 200:
            logger.info(f"✅ Visualization file accessible: {file_path}")
        else:
            logger.error(f"❌ Failed to access visualization file: {file_path}")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Response text: {response.text[:100]}...")
    
    logger.info("Visualization access test completed.")

def test_static_file_sync():
    """Test if static file changes are reflected immediately."""
    if not check_flask_app():
        pytest.skip("Flask app is not running. Skipping test.")
    
    # Create a temporary test file
    test_file_name = f"test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    test_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), f'static/{test_file_name}')
    
    try:
        # Create the test file
        with open(test_file_path, 'w') as f:
            f.write(f"Test content created at {datetime.now()}")
        
        logger.info(f"Created test file: {test_file_path}")
        
        # Test if the file is accessible
        response = requests.get(f'http://localhost:5004/static/{test_file_name}')
        
        if response.status_code == 200:
            logger.info(f"✅ Test file accessible: /static/{test_file_name}")
        else:
            logger.error(f"❌ Failed to access test file: /static/{test_file_name}")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Response text: {response.text[:100]}...")
    
    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            logger.info(f"Removed test file: {test_file_path}")
    
    logger.info("Static file sync test completed.")

def force_visualization_regeneration():
    """Force regeneration of visualizations to test the process."""
    if not check_flask_app():
        pytest.skip("Flask app is not running. Skipping test.")
    
    pdf_path = os.path.join(TEST_PDFS_DIR, 'test_visualization_form.pdf')
    if not os.path.exists(pdf_path):
        logger.error(f"Test PDF not found: {pdf_path}")
        return
    
    template_path = os.path.join(TEST_TEMPLATES_DIR, 'test_visualization_template.json')
    if not os.path.exists(template_path):
        logger.error(f"Test template not found: {template_path}")
        return
    
    # Load the template
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    # Prepare data for visualization request
    data = {
        'pdfPath': pdf_path,
        'template': template,
        'force': True
    }
    
    # Request visualization generation
    logger.info("Requesting visualization generation...")
    response = requests.post('http://localhost:5004/api/visualize', json=data)
    
    if response.status_code == 200:
        result = response.json()
        logger.info("✅ Visualization generation successful")
        logger.info(f"Visualization URL: {result.get('visualizationUrl')}")
        
        # Test if the visualization file is accessible
        viz_url = result.get('visualizationUrl')
        if viz_url:
            # Remove leading / if present
            if viz_url.startswith('/'):
                viz_url = viz_url[1:]
            
            viz_response = requests.get(f'http://localhost:5004/{viz_url}')
            
            if viz_response.status_code == 200:
                logger.info(f"✅ Generated visualization accessible: {viz_url}")
            else:
                logger.error(f"❌ Failed to access generated visualization: {viz_url}")
                logger.error(f"Status code: {viz_response.status_code}")
        
    else:
        logger.error("❌ Visualization generation failed")
        logger.error(f"Status code: {response.status_code}")
        logger.error(f"Response text: {response.text}")
    
    logger.info("Force visualization regeneration test completed.")

def run_tests():
    """Run all tests."""
    logger.info("Starting static path tests...")
    
    # Run tests
    test_static_file_access()
    test_visualization_access()
    test_static_file_sync()
    force_visualization_regeneration()
    
    logger.info("All static path tests completed.")

if __name__ == "__main__":
    run_tests() 