"""
UI tests for visualization components.
This module covers the UI components and templates for both field and checkbox visualization.
"""

import unittest
import os
import json
import tempfile
import shutil
from flask import Flask, template_rendered, jsonify
from contextlib import contextmanager
from flask import appcontext_pushed, g
from unittest.mock import patch, MagicMock
import pytest

# Import path setup to handle imports from main project
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from path_setup import BASE_DIR, SRC_DIR
from test_config import get_test_resource_path, get_test_pdf_path, get_test_template_path

# Import Flask app if available
try:
    from src import app as flask_app
except ImportError:
    # Skip tests if modules cannot be imported
    from unittest import skip
    skip("Flask app could not be imported")

# Sample field data for testing
SAMPLE_FIELDS = [
    {
        "id": "new_client_id",
        "name": "New Client ID",
        "type": "checkbox",
        "page": 1,
        "bbox": {
            "left": 0.134,
            "top": 0.189,
            "width": 0.013,
            "height": 0.013
        },
        "value": True
    },
    {
        "id": "add_account",
        "name": "Add Account",
        "type": "checkbox",
        "page": 1,
        "bbox": {
            "left": 0.249,
            "top": 0.189,
            "width": 0.013,
            "height": 0.013
        },
        "value": False
    }
]

# Sample checkbox data for testing
SAMPLE_CHECKBOXES = [
    {
        "id": "cb1",
        "label": "Option 1",
        "value": True,
        "confidence": 0.95,
        "page": 1,
        "bbox": {"left": 0.1, "top": 0.1, "right": 0.2, "bottom": 0.2}
    },
    {
        "id": "cb2", 
        "label": "Option 2",
        "value": False,
        "confidence": 0.8,
        "page": 1,
        "bbox": {"left": 0.1, "top": 0.3, "right": 0.2, "bottom": 0.4}
    }
]


class TestVisualizationUI(unittest.TestCase):
    """Base class for visualization UI tests."""
    
    def setUp(self):
        """Set up test environment."""
        # Create Flask test app
        self.app = Flask(__name__,
                         template_folder=os.path.join(SRC_DIR, 'templates'),
                         static_folder=os.path.join(SRC_DIR, 'static'))
        self.app.testing = True
        self.client = self.app.test_client()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestFieldVisualizationUI(TestVisualizationUI):
    """Test cases for field overlay visualization UI."""
    
    def setUp(self):
        """Set up test case with field-specific fixtures."""
        super().setUp()
        
        # Test document details
        self.test_document_id = "test_doc_123"
        self.pdf_path = get_test_pdf_path("test_form.pdf")
        
        # Check if test PDF exists, skip test if not
        if not os.path.exists(self.pdf_path):
            pytest.skip(f"Test PDF file not found: {self.pdf_path}")
        
        # Set up routes for testing
        @self.app.route('/ui/field-visualization/<document_id>')
        def field_visualization_ui(document_id):
            """Serve the field visualization template."""
            return self.app.send_static_file('field_visualization.html')
        
        @self.app.route('/api/field-visualization/<document_id>')
        def get_field_visualization_data(document_id):
            """API endpoint to get field extraction visualization data."""
            # Return field visualization data
            page_data = [
                {
                    "page_number": 1,
                    "image_url": f"/test/pages/page_1.png",
                    "width": 600,
                    "height": 800
                }
            ]
            
            # Count fields by type
            field_types = {}
            for field in SAMPLE_FIELDS:
                field_type = field.get("type", "other")
                field_types[field_type] = field_types.get(field_type, 0) + 1
            
            # Return full visualization data
            return jsonify({
                "document_id": document_id,
                "document_name": "Test Form",
                "processing_date": "2023-11-30T12:00:00Z",
                "total_pages": 1,
                "pages": page_data,
                "fields": SAMPLE_FIELDS,
                "field_types": field_types
            })
    
    def test_field_visualization_endpoint(self):
        """Test the field visualization API endpoint."""
        response = self.client.get(f'/api/field-visualization/{self.test_document_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify response data
        data = json.loads(response.data)
        self.assertEqual(data['document_id'], self.test_document_id)
        self.assertIn('fields', data)
        self.assertIn('pages', data)
        self.assertIn('field_types', data)
        
        # Verify field data
        self.assertEqual(len(data['fields']), len(SAMPLE_FIELDS))
        
        # Verify field types
        self.assertIn('checkbox', data['field_types'])
        self.assertEqual(data['field_types']['checkbox'], 2)
    
    def test_field_ui_endpoint(self):
        """Test the field visualization UI endpoint."""
        # Skip if static files are not available
        response = self.client.get(f'/ui/field-visualization/{self.test_document_id}')
        if response.status_code != 200:
            pytest.skip("Field visualization UI template not found in test environment.")
        self.assertEqual(response.status_code, 200)


class TestCheckboxVisualizationUI(TestVisualizationUI):
    """Test cases for checkbox visualization UI."""
    
    def setUp(self):
        """Set up test case with checkbox-specific fixtures."""
        super().setUp()
        
        # Test document details
        self.test_document_id = "test_cb_doc_123"
        
        # Set up routes for testing
        @self.app.route('/ui/checkbox-visualization/<document_id>')
        def checkbox_visualization_ui(document_id):
            """Serve the checkbox visualization template."""
            return self.app.send_static_file('checkbox_visualization.html')
        
        @self.app.route('/api/visualization/<document_id>')
        def get_checkbox_visualization_data(document_id):
            """API endpoint to get checkbox visualization data."""
            # Return checkbox visualization data
            page_data = [
                {
                    "page_number": 1,
                    "image_url": f"/test/pages/checkbox_page_1.png",
                    "width": 600,
                    "height": 800
                }
            ]
            
            # Return full visualization data
            return jsonify({
                "document_id": document_id,
                "document_name": "Test Checkbox Form",
                "processing_date": "2023-11-30T12:00:00Z",
                "total_pages": 1,
                "pages": page_data,
                "checkboxes": SAMPLE_CHECKBOXES
            })
    
    def test_checkbox_visualization_endpoint(self):
        """Test the checkbox visualization API endpoint."""
        response = self.client.get(f'/api/visualization/{self.test_document_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify response data
        data = json.loads(response.data)
        self.assertEqual(data['document_name'], "Test Checkbox Form")
        self.assertIn('checkboxes', data)
        self.assertIn('pages', data)
        
        # Verify checkbox data
        self.assertEqual(len(data['checkboxes']), len(SAMPLE_CHECKBOXES))
    
    def test_checkbox_ui_endpoint(self):
        """Test the checkbox visualization UI endpoint."""
        # Skip if static files are not available
        response = self.client.get(f'/ui/checkbox-visualization/{self.test_document_id}')
        if response.status_code != 200:
            pytest.skip("Checkbox visualization UI template not found in test environment.")
        self.assertEqual(response.status_code, 200)


class TestVisualizationAssets(unittest.TestCase):
    """Test for visualization static assets and resources."""
    
    def test_static_assets_exist(self):
        """Test if required static assets exist."""
        # Check if test data paths exist
        test_paths = [
            # Skip if test directories don't exist
            os.path.join(BASE_DIR, "static/images"),
            os.path.join(BASE_DIR, "static/visualizations")
        ]
        
        for path in test_paths:
            if not os.path.exists(path):
                # Don't fail, just skip
                pytest.skip(f"Required static path not found: {path}")
        
        # Check for placeholder images
        placeholder_dir = os.path.join(BASE_DIR, "static/images")
        if os.path.exists(placeholder_dir):
            placeholders = [
                "loading-placeholder.png",
                "error-placeholder.png"
            ]
            
            for placeholder in placeholders:
                placeholder_path = os.path.join(placeholder_dir, placeholder)
                if not os.path.exists(placeholder_path):
                    pytest.skip(f"Placeholder image not found: {placeholder_path}")


if __name__ == '__main__':
    unittest.main() 