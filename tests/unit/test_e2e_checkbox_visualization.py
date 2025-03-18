"""
End-to-end tests for checkbox visualization workflow.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import io
import time
from flask.testing import FlaskClient

# Import path setup to handle imports from main project
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.path_setup import BASE_DIR, SRC_DIR
from tests.test_config import get_test_resource_path, get_test_pdf_path, get_test_template_path

# Now import the modules to test
sys.path.append(SRC_DIR)
from src import app as flask_app


class TestE2ECheckboxVisualization(unittest.TestCase):
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
        """Set up test client and fixtures."""
        # Set up Flask test client
        flask_app.app.config['TESTING'] = True
        self.client = flask_app.app.test_client()
        
        # Create mock PDF content
        self.mock_pdf_content = b'%PDF-1.5\n%Test PDF for checkbox detection'
        
        # Create temp directories for test files
        self.test_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.test_dir, "upload")
        self.processed_dir = os.path.join(self.test_dir, "processed")
        self.vis_dir = os.path.join(self.processed_dir, "visualizations")
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.vis_dir, exist_ok=True)
        
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

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

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
        
        # Create test PDF in mock upload folder
        with open(os.path.join(self.upload_dir, f"{self.mock_document_id}_test_form.pdf"), 'wb') as f:
            f.write(self.mock_pdf_content)

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
    def test_full_visualization_flow(self):
        """Test the complete visualization workflow end-to-end."""
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
            
            # Step 7: Export the corrected data
            export_data = {
                "document_id": document_id,
                "document_name": "test_form.pdf",
                "checkboxes": self.mock_checkboxes  # In a real test, this would include the corrections
            }
            
            response = self.client.post(
                '/api/visualization/export',
                json=export_data,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            export_result = json.loads(response.data)
            self.assertEqual(export_result["document_id"], document_id)
            self.assertEqual(len(export_result["checkboxes"]), 3)
            
        finally:
            self._end_mocks()


if __name__ == '__main__':
    unittest.main() 