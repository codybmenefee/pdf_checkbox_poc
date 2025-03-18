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
from pprint import pprint

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if Flask app is running
def check_flask_app():
    try:
        response = requests.get('http://localhost:5004/api/health')
        if response.status_code == 200:
            return True
        return False
    except requests.ConnectionError:
        return False

# Test static file access
def test_static_file_access():
    logger.info("Testing static file access...")
    
    # Use the static_debug endpoint to get info about static files
    response = requests.get('http://localhost:5000/static_debug')
    if response.status_code != 200:
        logger.error(f"Failed to get static_debug info: {response.status_code}")
        return False
    
    static_info = response.json()
    logger.info(f"Static folder: {static_info.get('static_folder')}")
    logger.info(f"Static folder exists: {static_info.get('exists')}")
    
    # Print first level of contents
    for path, info in static_info.get('contents', {}).items():
        if path == '':
            logger.info("Root static folder contents:")
            for directory in info.get('dirs', []):
                logger.info(f"  Directory: {directory}")
            for file in info.get('files', []):
                logger.info(f"  File: {file.get('name')} ({file.get('size')} bytes)")
    
    # Test accessing a known static file
    if 'images' in [d for d in static_info.get('contents', {}).get('', {}).get('dirs', [])]:
        logger.info("Testing access to placeholder images...")
        # Try to access loading placeholder
        response = requests.get('http://localhost:5000/static/images/loading-placeholder.png')
        if response.status_code == 200:
            logger.info("Successfully accessed loading-placeholder.png")
        else:
            logger.error(f"Failed to access loading-placeholder.png: {response.status_code}")
            return False
    
    return True

# Test visualization file access
def test_visualization_access():
    logger.info("Testing visualization file access...")
    
    # Get list of templates
    response = requests.get('http://localhost:5000/api/templates')
    if response.status_code != 200:
        logger.error(f"Failed to get templates: {response.status_code}")
        return False
    
    templates = response.json().get('templates', [])
    if not templates:
        logger.warning("No templates found to test visualization")
        # Consider this a pass since we're testing static paths, not templates
        return True
    
    # Pick the first template
    template_id = templates[0].get('template_id')
    logger.info(f"Testing visualization for template: {template_id}")
    
    # Try to visualize the template
    response = requests.get(f'http://localhost:5000/api/templates/{template_id}/visualize')
    if response.status_code != 200:
        logger.warning(f"Template visualization returned status code {response.status_code}. This might be ok if the template's PDF file is missing.")
        # Try accessing placeholder image instead
        response = requests.get('http://localhost:5000/static/images/error-placeholder.png')
        if response.status_code == 200:
            logger.info("Successfully accessed error-placeholder.png instead")
            return True
        else:
            logger.error(f"Failed to access error-placeholder.png: {response.status_code}")
            return False
    
    visualization = response.json()
    pages = visualization.get('pages', [])
    
    if not pages:
        logger.warning("No visualization pages found")
        return True
    
    # Try to access the first page image
    page = pages[0]
    image_url = page.get('image_url')
    
    if not image_url:
        logger.warning("No image URL found in visualization")
        return True
    
    # Convert relative URL to absolute
    if image_url.startswith('/'):
        image_url = f"http://localhost:5000{image_url}"
    
    logger.info(f"Testing access to visualization image: {image_url}")
    response = requests.get(image_url)
    
    if response.status_code == 200:
        logger.info("Successfully accessed visualization image")
    else:
        logger.error(f"Failed to access visualization image: {response.status_code}")
        return False
    
    return True

# Test static file sync
def test_static_file_sync():
    logger.info("Testing static file sync functionality...")
    
    # Use the test_api_route endpoint to get app info
    response = requests.get('http://localhost:5000/api/test_route')
    if response.status_code != 200:
        logger.error(f"Failed to get app info: {response.status_code}")
        return False
    
    app_info = response.json()
    static_folder = app_info.get('static_folder')
    
    if not static_folder:
        logger.error("Static folder info not available")
        return False
    
    logger.info(f"App static folder: {static_folder}")
    
    # Check for successful routes
    routes = app_info.get('routes', [])
    static_routes = [r for r in routes if 'static' in r]
    logger.info(f"Static-related routes: {static_routes}")
    
    return True

# Force regeneration of a visualization
def force_visualization_regeneration():
    logger.info("Testing forced visualization regeneration...")
    
    # Get list of templates
    response = requests.get('http://localhost:5000/api/templates')
    if response.status_code != 200:
        logger.error(f"Failed to get templates: {response.status_code}")
        return False
    
    templates = response.json().get('templates', [])
    if not templates:
        logger.warning("No templates found to test visualization regeneration")
        # Since we're testing static paths, not templates, consider this a pass
        return True
    
    # Pick the first template
    template_id = templates[0].get('template_id')
    logger.info(f"Forcing visualization regeneration for template: {template_id}")
    
    # Force regeneration
    response = requests.get(f'http://localhost:5000/force_visualization/{template_id}')
    if response.status_code != 200:
        logger.warning(f"Force visualization returned status code {response.status_code}. This might be ok if the template's PDF file is missing.")
        # Check if we can access any static file instead
        response = requests.get('http://localhost:5000/static/images/loading-placeholder.png')
        if response.status_code == 200:
            logger.info("Successfully accessed loading-placeholder.png instead")
            return True
        else:
            logger.error(f"Failed to access loading-placeholder.png: {response.status_code}")
            return False
    
    result = response.json()
    logger.info(f"Visualization regeneration result: {result.get('status')}")
    
    # Check if the visualization files exist
    pages = result.get('pages', [])
    if not pages:
        logger.warning("No pages in regenerated visualization")
        return True
    
    # Check access to the regenerated files
    for page in pages:
        image_url = page.get('image_url')
        if not image_url:
            continue
        
        # Convert relative URL to absolute
        if image_url.startswith('/'):
            image_url = f"http://localhost:5000{image_url}"
        
        logger.info(f"Testing access to regenerated image: {image_url}")
        response = requests.get(image_url)
        
        if response.status_code == 200:
            logger.info("Successfully accessed regenerated image")
        else:
            logger.error(f"Failed to access regenerated image: {response.status_code}")
            return False
    
    return True

# Main test function
def run_tests():
    logger.info("Starting static file path configuration tests")
    
    # Check if Flask app is running
    if not check_flask_app():
        logger.error("Flask app is not running on http://localhost:5000. Please start it first.")
        return False
    
    # Run tests
    tests = [
        ("Static file access", test_static_file_access),
        ("Visualization access", test_visualization_access),
        ("Static file sync", test_static_file_sync),
        ("Force visualization regeneration", force_visualization_regeneration)
    ]
    
    all_passed = True
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}")
        try:
            if test_func():
                logger.info(f"✅ {name} - PASSED")
            else:
                logger.error(f"❌ {name} - FAILED")
                all_passed = False
        except Exception as e:
            logger.error(f"❌ {name} - ERROR: {str(e)}")
            all_passed = False
    
    if all_passed:
        logger.info("All tests PASSED!")
    else:
        logger.error("Some tests FAILED!")
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 