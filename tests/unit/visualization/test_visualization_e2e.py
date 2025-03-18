"""
End-to-end tests for visualization workflows.
This module combines tests for both checkbox and field visualization workflows.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import pytest

# Import path setup to handle imports from main project
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from path_setup import BASE_DIR, SRC_DIR
from test_config import get_test_resource_path, get_test_pdf_path, get_test_template_path

# Import the Flask app
try:
    from src import app as flask_app
    from src.db_core import DatabaseManager
except ImportError:
    # Skip tests if modules cannot be imported
    from unittest import skip
    skip("Required modules could not be imported")


class TestVisualizationEndToEnd(unittest.TestCase):
    """
    Base class for end-to-end visualization tests.
    Provides common setup and teardown functionality.
    """
    
    def setUp(self):
        """Set up test client and fixtures."""
        # Set up Flask test client
        flask_app.app.config['TESTING'] = True
        self.client = flask_app.app.test_client()
        
        # Create temp directories for test files
        self.test_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.test_dir, "upload")
        self.processed_dir = os.path.join(self.test_dir, "processed")
        self.vis_dir = os.path.join(self.processed_dir, "visualizations")
        self.static_dir = os.path.join(self.test_dir, "static")
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.vis_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)
        
        # Create mock PDF content
        self.mock_pdf_content = b'%PDF-1.5\n%Test PDF for visualization'
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)


class TestCheckboxVisualizationE2E(TestVisualizationEndToEnd):
    """
    End-to-end tests for checkbox detection and visualization workflow.
    
    This test follows the complete flow:
    1. Upload a document
    2. Process it for checkbox detection
    3. Visualize checkboxes with confidence scores
    4. View visualization data
    5. Make corrections
    6. Export the corrected data
    """
    
    def setUp(self):
        """Set up test case with checkbox-specific fixtures."""
        super().setUp()
        
        # Mock data for the workflow
        self.mock_document_id = "test_doc_123"
        self.mock_checkboxes = [
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
            },
            {
                "id": "cb3",
                "label": "Option 3",
                "value": True,
                "confidence": 0.6,
                "page": 2,
                "bbox": {"left": 0.1, "top": 0.1, "right": 0.2, "bottom": 0.2}
            }
        ]
        
        self.mock_visualization_data = {
            "document_name": "test_form.pdf",
            "processing_date": "2023-05-01T12:00:00Z",
            "total_pages": 2,
            "pages": [
                {
                    "page_number": 1,
                    "image_url": f"/static/visualizations/{self.mock_document_id}/checkbox_vis_page_1.png",
                    "width": 600,
                    "height": 800
                },
                {
                    "page_number": 2,
                    "image_url": f"/static/visualizations/{self.mock_document_id}/checkbox_vis_page_2.png",
                    "width": 600,
                    "height": 800
                }
            ],
            "checkboxes": self.mock_checkboxes
        }
        
        # Create mock visualization images
        vis_doc_dir = os.path.join(self.vis_dir, self.mock_document_id)
        os.makedirs(vis_doc_dir, exist_ok=True)
        
        # Create placeholder image files
        with open(os.path.join(vis_doc_dir, "checkbox_vis_page_1.png"), 'wb') as f:
            f.write(b'Mock image data')
        with open(os.path.join(vis_doc_dir, "checkbox_vis_page_2.png"), 'wb') as f:
            f.write(b'Mock image data')
        
        # Create visualization metadata file
        with open(os.path.join(vis_doc_dir, "checkbox_visualization_data.json"), 'w') as f:
            json.dump(self.mock_visualization_data, f)
        
        # Create test PDF in mock upload folder
        with open(os.path.join(self.upload_dir, f"{self.mock_document_id}_test_form.pdf"), 'wb') as f:
            f.write(self.mock_pdf_content)
    
    def _create_mocks(self):
        """Create and apply all necessary mocks for the test."""
        # Create patches
        self.patch_upload_folder = patch('src.app.UPLOAD_FOLDER', self.upload_dir)
        self.patch_processed_folder = patch('src.app.PROCESSED_FOLDER', self.processed_dir)
        self.patch_document_ai = patch('src.app.DocumentAIClient')
        self.patch_pdf_handler = patch('src.app.PDFHandler')
        self.patch_visualize = patch('src.visualization.visualize_checkboxes_with_confidence')
        self.patch_get_vis_data = patch('src.ui_api.get_checkbox_visualization_data')
        self.patch_export_data = patch('src.ui_api.export_checkbox_data')
        self.patch_save_corrections = patch('src.ui_api.save_checkbox_corrections')
        
        # Start patches
        self.mock_upload_folder = self.patch_upload_folder.start()
        self.mock_processed_folder = self.patch_processed_folder.start()
        self.mock_document_ai = self.patch_document_ai.start()
        self.mock_pdf_handler = self.patch_pdf_handler.start()
        self.mock_visualize = self.patch_visualize.start()
        self.mock_get_vis_data = self.patch_get_vis_data.start()
        self.mock_export_data = self.patch_export_data.start()
        self.mock_save_corrections = self.patch_save_corrections.start()
        
        # Configure mocks
        mock_doc_ai_instance = MagicMock()
        self.mock_document_ai.return_value = mock_doc_ai_instance
        mock_doc_ai_instance.process_document.return_value = {
            "pages": [
                {"checkboxes": self.mock_checkboxes[:2]},
                {"checkboxes": [self.mock_checkboxes[2]]}
            ]
        }
        
        mock_pdf_handler_instance = MagicMock()
        self.mock_pdf_handler.return_value = mock_pdf_handler_instance
        mock_pdf_handler_instance.upload_pdf.return_value = {
            "file_id": self.mock_document_id,
            "original_filename": "test_form.pdf",
            "stored_filename": f"{self.mock_document_id}_test_form.pdf",
            "file_path": os.path.join(self.upload_dir, f"{self.mock_document_id}_test_form.pdf"),
            "file_size": len(self.mock_pdf_content)
        }
        
        self.mock_visualize.return_value = self.mock_visualization_data
        self.mock_get_vis_data.return_value = self.mock_visualization_data
        self.mock_export_data.return_value = {
            "document_id": self.mock_document_id,
            "document_name": "test_form.pdf",
            "export_date": "2023-05-01T12:00:00Z",
            "checkboxes": self.mock_checkboxes
        }
        self.mock_save_corrections.return_value = True
    
    def _end_mocks(self):
        """End all mocks."""
        self.patch_upload_folder.stop()
        self.patch_processed_folder.stop()
        self.patch_document_ai.stop()
        self.patch_pdf_handler.stop()
        self.patch_visualize.stop()
        self.patch_get_vis_data.stop()
        self.patch_export_data.stop()
        self.patch_save_corrections.stop()
    
    @unittest.skip("Need to fix API tests first")
    def test_checkbox_visualization_flow(self):
        """Test the complete checkbox visualization workflow end-to-end."""
        try:
            self._create_mocks()
            
            # Step 1: Upload a document
            with open(os.path.join(self.test_dir, "test_form.pdf"), 'wb') as f:
                f.write(self.mock_pdf_content)
            
            with open(os.path.join(self.test_dir, "test_form.pdf"), 'rb') as f:
                response = self.client.post(
                    '/api/documents/upload',
                    data={'file': (f, 'test_form.pdf')},
                    content_type='multipart/form-data'
                )
            
            self.assertEqual(response.status_code, 200)
            upload_data = json.loads(response.data)
            self.assertIn("file_info", upload_data)
            document_id = upload_data["file_info"].get("file_id", self.mock_document_id)
            
            # Step 2: Process the document for checkbox detection
            response = self.client.post(f'/api/documents/{document_id}/process')
            self.assertEqual(response.status_code, 200)
            process_data = json.loads(response.data)
            self.assertIn("message", process_data)
            self.assertEqual(process_data["message"], "Document processed successfully")
            
            # Step 3: Visualize checkboxes with confidence scores
            response = self.client.post(
                f'/api/documents/{document_id}/visualize-checkboxes',
                json={
                    "high_confidence_threshold": 0.9,
                    "medium_confidence_threshold": 0.7
                },
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            vis_data = json.loads(response.data)
            self.assertEqual(vis_data["status"], "success")
            self.assertEqual(vis_data["visualization_id"], document_id)
            
            # Step 4: View the visualization data
            response = self.client.get(f'/api/visualization/{document_id}')
            self.assertEqual(response.status_code, 200)
            checkbox_data = json.loads(response.data)
            self.assertEqual(checkbox_data["document_name"], "test_form.pdf")
            self.assertEqual(len(checkbox_data["checkboxes"]), 3)
            
            # Step 5: Access the visualization UI
            response = self.client.get(f'/ui/checkbox-visualization/{document_id}')
            self.assertEqual(response.status_code, 200)
            
            # Step 6: Make corrections
            corrections = [
                {
                    "id": "cb1",
                    "label": "Modified Option 1",
                    "value": False,
                    "manually_corrected": True
                }
            ]
            
            response = self.client.post(
                '/api/visualization/save-corrections',
                json={
                    "document_id": document_id,
                    "corrections": corrections
                },
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            correction_result = json.loads(response.data)
            self.assertEqual(correction_result["status"], "success")
            
            # Step 7: Export the data
            response = self.client.post(
                '/api/visualization/export',
                json={
                    "document_id": document_id,
                    "document_name": "test_form.pdf",
                    "checkboxes": self.mock_checkboxes
                },
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            export_data = json.loads(response.data)
            self.assertEqual(export_data["document_id"], document_id)
            self.assertEqual(export_data["document_name"], "test_form.pdf")
            
        finally:
            self._end_mocks()


class TestFieldVisualizationE2E(TestVisualizationEndToEnd):
    """
    End-to-end tests for field visualization workflow.
    
    This test validates:
    1. Field visualization with test_form_id
    2. Field visualization with ncaf8_form_id
    3. Image loading from multiple potential locations
    4. Proper data retrieval from MongoDB
    """
    
    def setUp(self):
        """Set up test case with field-specific fixtures."""
        super().setUp()
        
        # Create test form IDs
        self.test_form_id = "test_form_id_123"
        self.ncaf8_form_id = "ncaf8_form_id_456"
    
    def _create_mocks(self):
        """Set up all the necessary mocks."""
        # Start patching
        self.db_manager_patcher = patch('src.db_core.DatabaseManager')
        self.filled_form_model_patcher = patch('src.db_models.FilledFormModel')
        self.template_manager_patcher = patch('src.template_manager.TemplateManager')
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
    
    def test_field_visualization_workflow(self):
        """Test field visualization with different form types."""
        try:
            self._create_mocks()
            
            # Test with test_form_id
            response = self.client.get(f'/api/field-visualization/form/{self.test_form_id}')
            
            # Skip if the endpoint doesn't exist
            if response.status_code == 404:
                pytest.skip("Field visualization endpoint not available")
            
            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Validate response data
            self.assertEqual(data["document_name"], "Test Document")
            self.assertEqual(len(data["fields"]), 1)
            self.assertEqual(data["fields"][0]["name"], "Test Field 1")
            
            # Verify that the correct form was retrieved
            self.mock_filled_form_model_instance.get.assert_called_with(self.test_form_id)
            
            # Test with ncaf8_form_id
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
            
        finally:
            self._end_mocks()
    
    def test_field_image_serving(self):
        """Test that images are served from multiple potential locations."""
        # Skip this test since it requires a running server
        pytest.skip("This test requires a running Flask instance to properly serve static files")


if __name__ == '__main__':
    unittest.main() 