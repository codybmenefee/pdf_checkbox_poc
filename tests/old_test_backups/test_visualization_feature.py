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
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_directories():
    """Check if required directories exist."""
    required_dirs = [
        "data/templates",
        "data/test_pdfs",
        "static/images",
        "static/visualizations"
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

def check_template():
    """Check if test template exists and is valid."""
    template_path = "data/templates/test_visualization_template.json"
    
    if not os.path.exists(template_path):
        logger.error(f"Test template not found: {template_path}")
        return False
    
    try:
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        # Check required fields
        required_fields = ["template_id", "name", "fields", "document"]
        for field in required_fields:
            if field not in template:
                logger.error(f"Template missing required field: {field}")
                return False
        
        # Check if fields are properly defined
        if not template["fields"]:
            logger.error("Template has no fields defined")
            return False
        
        # Check sample field structure
        sample_field = template["fields"][0]
        required_field_props = ["field_id", "field_type", "bbox", "page"]
        for prop in required_field_props:
            if prop not in sample_field:
                logger.error(f"Fields missing required property: {prop}")
                return False
        
        # Check if document info is properly defined
        if "original_filename" not in template["document"]:
            logger.error("Template document missing original_filename")
            return False
        
        logger.info(f"Template validation successful: {len(template['fields'])} fields found")
        return True
        
    except Exception as e:
        logger.error(f"Error validating template: {str(e)}")
        return False

def check_test_pdf():
    """Check if test PDF exists."""
    if not os.path.exists("data/templates/test_visualization_template.json"):
        logger.error("Cannot check PDF without template")
        return False
        
    with open("data/templates/test_visualization_template.json", 'r') as f:
        template = json.load(f)
    
    original_filename = template["document"]["original_filename"]
    pdf_path = f"data/test_pdfs/{original_filename}"
    
    if not os.path.exists(pdf_path):
        logger.error(f"Test PDF not found: {pdf_path}")
        return False
    
    logger.info(f"Test PDF found: {pdf_path}")
    return True

def check_placeholder_images():
    """Check if placeholder images exist."""
    required_images = [
        "loading-placeholder.png",
        "error-placeholder.png", 
        "no-content.png"
    ]
    
    missing_images = []
    for image in required_images:
        image_path = f"static/images/{image}"
        if not os.path.exists(image_path):
            missing_images.append(image)
    
    if missing_images:
        logger.error(f"Missing placeholder images: {', '.join(missing_images)}")
        logger.info("You need to run generate_placeholders.py to create these images")
        return False
    
    logger.info("All placeholder images found")
    return True

def create_test_visualization():
    """Create a test visualization for the test template."""
    if not check_template() or not check_test_pdf():
        logger.error("Cannot create test visualization without template and PDF")
        return False
    
    try:
        from src.visualization import visualize_extracted_fields
        
        # Load the template
        with open("data/templates/test_visualization_template.json", 'r') as f:
            template = json.load(f)
        
        # Prepare visualization directory
        vis_id = template["template_id"]
        output_dir = os.path.join("static", "visualizations", vis_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Get PDF path
        pdf_path = os.path.join("data", "test_pdfs", template["document"]["original_filename"])
        
        # Create visualization
        result = visualize_extracted_fields(pdf_path, template["fields"], output_dir)
        
        # Check if visualization was created successfully
        if "error" in result:
            logger.error(f"Visualization creation failed: {result.get('error_message', 'Unknown error')}")
            return False
        
        logger.info(f"Test visualization created: {len(result['pages'])} pages, {len(result['fields'])} fields")
        
        # Save visualization metadata
        metadata_path = os.path.join(output_dir, "metadata.json")
        if os.path.exists(metadata_path):
            logger.info(f"Visualization metadata saved to: {metadata_path}")
            return True
        else:
            logger.error("Visualization metadata not created")
            return False
        
    except ImportError:
        logger.error("Cannot import visualization module - run this script from the project root")
        return False
    except Exception as e:
        logger.error(f"Error creating test visualization: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting PDF field visualization tests")
    
    tests = [
        ("Directory structure check", check_directories),
        ("Template validation", check_template),
        ("Test PDF check", check_test_pdf),
        ("Placeholder images check", check_placeholder_images),
        ("Test visualization creation", create_test_visualization)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            if test_func():
                logger.info(f"✓ {test_name} - PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} - FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} - FAILED with exception: {str(e)}")
            failed += 1
    
    logger.info(f"Tests completed: {passed} passed, {failed} failed")
    
    # Summary message
    if failed == 0:
        logger.info("All tests passed! The PDF field visualization feature is ready to use.")
        logger.info("You can access the test visualization at /ui/template-advanced-visualization/test-visualization-template")
    else:
        logger.warning("Some tests failed. Please fix the issues before proceeding.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 