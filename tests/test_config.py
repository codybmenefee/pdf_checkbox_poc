"""
Configuration for tests, including paths to test data.
"""
import os

# Import path setup to ensure modules can be imported
from path_setup import BASE_DIR

# Base directories
TESTS_DIR = os.path.join(BASE_DIR, 'tests')

# Test data directories
TEST_DATA_DIR = os.path.join(TESTS_DIR, 'data')
TEST_PDFS_DIR = os.path.join(TEST_DATA_DIR, 'pdfs')
TEST_TEMPLATES_DIR = os.path.join(TEST_DATA_DIR, 'templates')

# Common test files
TEST_VISUALIZATION_PDF = os.path.join(TEST_PDFS_DIR, 'test_visualization_form.pdf')
TEST_VISUALIZATION_TEMPLATE = os.path.join(TEST_TEMPLATES_DIR, 'test_visualization_template.json')

# Function to get absolute path for a test resource
def get_test_resource_path(relative_path):
    """
    Get absolute path for a test resource file
    
    Args:
        relative_path (str): Path relative to the test data directory
        
    Returns:
        str: Absolute path to the resource
    """
    return os.path.join(TEST_DATA_DIR, relative_path)

# Function to get path for a test PDF
def get_test_pdf_path(pdf_filename):
    """
    Get path for a test PDF file
    
    Args:
        pdf_filename (str): PDF filename
        
    Returns:
        str: Path to the PDF file
    """
    return os.path.join(TEST_PDFS_DIR, pdf_filename)

# Function to get path for a test template
def get_test_template_path(template_filename):
    """
    Get path for a test template file
    
    Args:
        template_filename (str): Template filename
        
    Returns:
        str: Path to the template file
    """
    return os.path.join(TEST_TEMPLATES_DIR, template_filename) 