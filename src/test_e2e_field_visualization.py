"""
End-to-end tests for field visualization workflow.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import requests
import time
from flask.testing import FlaskClient

from src import app as flask_app
from src.db_models import FilledFormModel
from src.db_core import DatabaseManager


class TestFieldVisualizationE2E(unittest.TestCase):
    """
    End-to-end tests for field visualization workflow.
    
    This test validates:
    1. Field visualization with test_form_id
    2. Field visualization with ncaf8_form_id
    3. Image loading from multiple potential locations
    4. Proper data retrieval from MongoDB
    """

    def setUp(self):
        """Set up test client and fixtures."""
        # Set up Flask test client
        flask_app.app.config['TESTING'] = True
        self.client = flask_app.app.test_client()
        
        # Create test form IDs
        self.test_form_id = "test_form_id_123"
        self.ncaf8_form_id = "ncaf8_form_id_456"
        
        # Set up temp directories
        self.test_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.test_dir, "upload")
        self.static_dir = os.path.join(self.test_dir, "static")
        self.vis_dir = os.path.join(self.static_dir, "visualizations")
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.vis_dir, exist_ok=True)
        
        # Create mock data
        self._create_mocks()
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory
        shutil.rmtree(self.test_dir)
        
        # End mocks
        self._end_mocks()
        
    def _create_mocks(self):
        """Set up all the necessary mocks."""
        # Start patching
        self.db_manager_patcher = patch('src.ui_api.DatabaseManager')
        self.filled_form_model_patcher = patch('src.ui_api.FilledFormModel')
        self.template_manager_patcher = patch('src.ui_api.TemplateManager')
        self.visualize_fields_patcher = patch('src.ui_api.visualize_extracted_fields')
        self.path_exists_patcher = patch('src.ui_api.os.path.exists')
        
        # Get mock objects
        self.mock_db_manager = self.db_manager_patcher.start()
        self.mock_filled_form_model = self.filled_form_model_patcher.start()
        self.mock_template_manager = self.template_manager_patcher.start()
        self.mock_visualize_fields = self.visualize_fields_patcher.start()
        self.mock_path_exists = self.path_exists_patcher.start()
        
        # Configure mocks
        
        # Mock DB manager
        self.mock_db_manager_instance = MagicMock()
        self.mock_db_manager.return_value = self.mock_db_manager_instance
        
        # Mock filled form model
        self.mock_filled_form_model_instance = MagicMock()
        self.mock_filled_form_model.return_value = self.mock_filled_form_model_instance
        
        # Mock template manager
        self.mock_template_manager_instance = MagicMock()
        self.mock_template_manager.return_value = self.mock_template_manager_instance
        
        # Create mock test form data
        self.test_form_data = {
            "form_id": self.test_form_id,
            "template_id": "test_template_id",
            "document": {
                "stored_filename": "test_document.pdf",
                "original_filename": "test.pdf"
            }
        }
        
        # Create mock NCAF-8 form data
        self.ncaf8_form_data = {
            "form_id": self.ncaf8_form_id,
            "template_id": "ncaf8_template_id",
            "document": {
                "stored_filename": "ncaf8_document.pdf",
                "original_filename": "NCAF8.pdf"
            }
        }
        
        # Mock template data
        self.test_template_data = {
            "template_id": "test_template_id",
            "fields": [
                {
                    "id": "field1",
                    "name": "Test Field 1",
                    "type": "checkbox",
                    "page": 1,
                    "bbox": {"left": 0.1, "top": 0.1, "width": 0.05, "height": 0.05}
                }
            ]
        }
        
        self.ncaf8_template_data = {
            "template_id": "ncaf8_template_id",
            "fields": [
                {
                    "id": "field1",
                    "name": "NCAF8 Field 1",
                    "type": "checkbox",
                    "page": 1,
                    "bbox": {"left": 0.2, "top": 0.2, "width": 0.05, "height": 0.05}
                }
            ]
        }
        
        # Mock visualization data
        self.test_visualization_data = {
            "document_name": "Test Document",
            "processing_date": "2023-01-01T12:00:00",
            "total_pages": 1,
            "pages": [
                {
                    "page_number": 1, 
                    "width": 612, 
                    "height": 792,
                    "image_url": f"/{self.test_form_id}/page_1.png"
                }
            ],
            "fields": self.test_template_data["fields"]
        }
        
        self.ncaf8_visualization_data = {
            "document_name": "NCAF8 Document",
            "processing_date": "2023-01-01T12:00:00",
            "total_pages": 1,
            "pages": [
                {
                    "page_number": 1, 
                    "width": 612, 
                    "height": 792,
                    "image_url": f"/{self.ncaf8_form_id}/page_1.png"
                }
            ],
            "fields": self.ncaf8_template_data["fields"]
        }
        
        # Configure mock behavior
        self.mock_filled_form_model_instance.get.side_effect = lambda form_id: self.test_form_data if form_id == self.test_form_id else self.ncaf8_form_data if form_id == self.ncaf8_form_id else None
        
        self.mock_template_manager_instance.get_template.side_effect = lambda template_id: self.test_template_data if template_id == "test_template_id" else self.ncaf8_template_data if template_id == "ncaf8_template_id" else None
        
        self.mock_visualize_fields.side_effect = lambda pdf_path, fields, output_dir: self.test_visualization_data if self.test_form_id in output_dir else self.ncaf8_visualization_data if self.ncaf8_form_id in output_dir else None
        
        self.mock_path_exists.return_value = True
        
    def _end_mocks(self):
        """End all patches."""
        self.db_manager_patcher.stop()
        self.filled_form_model_patcher.stop()
        self.template_manager_patcher.stop()
        self.visualize_fields_patcher.stop()
        self.path_exists_patcher.stop()
    
    def test_test_form_visualization(self):
        """Test visualization with test_form_id."""
        # Make API request
        response = self.client.get(f'/api/field-visualization/form/{self.test_form_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Validate response data
        self.assertEqual(data["document_name"], "Test Document")
        self.assertEqual(len(data["fields"]), 1)
        self.assertEqual(data["fields"][0]["name"], "Test Field 1")
        
        # Verify that the correct form was retrieved
        self.mock_filled_form_model_instance.get.assert_called_with(self.test_form_id)
        
        # Verify template was retrieved
        self.mock_template_manager_instance.get_template.assert_called_with("test_template_id")
    
    def test_ncaf8_form_visualization(self):
        """Test visualization with ncaf8_form_id."""
        # Make API request
        response = self.client.get(f'/api/field-visualization/form/{self.ncaf8_form_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Validate response data
        self.assertEqual(data["document_name"], "NCAF8 Document")
        self.assertEqual(len(data["fields"]), 1)
        self.assertEqual(data["fields"][0]["name"], "NCAF8 Field 1")
        
        # Verify that the correct form was retrieved
        self.mock_filled_form_model_instance.get.assert_called_with(self.ncaf8_form_id)
        
        # Verify template was retrieved
        self.mock_template_manager_instance.get_template.assert_called_with("ncaf8_template_id")
    
    def test_image_path_resolution(self):
        """Test that images are served from multiple potential locations."""
        # This would need to be tested with a running server in a real environment
        # For unit testing purposes, we can verify that the route exists and handles various paths
        
        with patch('src.app.send_file') as mock_send_file:
            # Mock send_file to return a simple response
            mock_send_file.return_value = "File content"
            
            # Test various visualization image requests
            vis_id = "test_vis_id"
            filename = "page_1.png"
            
            response = self.client.get(f'/static/visualizations/{vis_id}/{filename}')
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main() 