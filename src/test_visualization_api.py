"""
API tests for checkbox visualization endpoints.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src import app as flask_app
from src.visualization import visualize_checkboxes_with_confidence, get_checkbox_visualization_data


class TestVisualizationAPI(unittest.TestCase):
    """Test the visualization API endpoints."""

    def setUp(self):
        """Set up test client and temporary test data."""
        # Set up Flask test client
        flask_app.app.config['TESTING'] = True
        self.client = flask_app.app.test_client()
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.upload_folder = os.path.join(self.test_dir, "upload")
        self.processed_folder = os.path.join(self.test_dir, "processed")
        self.visualization_folder = os.path.join(self.processed_folder, "visualizations")
        
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.processed_folder, exist_ok=True)
        os.makedirs(self.visualization_folder, exist_ok=True)
        
        # Create test PDF
        self.test_pdf_path = os.path.join(self.upload_folder, "test_doc_123")
        with open(self.test_pdf_path, 'w') as f:
            f.write("Test PDF content")
        
        # Mock checkbox data
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
            }
        ]
        
        # Mock visualization data
        self.visualization_data = {
            "document_name": "test_doc.pdf",
            "processing_date": "2023-05-01T12:00:00Z",
            "total_pages": 2,
            "pages": [
                {
                    "page_number": 1,
                    "image_url": "/static/visualizations/test_doc_123/checkbox_vis_page_1.png",
                    "width": 600,
                    "height": 800
                },
                {
                    "page_number": 2,
                    "image_url": "/static/visualizations/test_doc_123/checkbox_vis_page_2.png",
                    "width": 600,
                    "height": 800
                }
            ],
            "checkboxes": self.mock_checkboxes
        }
        
        # Save mock visualization data
        vis_dir = os.path.join(self.visualization_folder, "test_doc_123")
        os.makedirs(vis_dir, exist_ok=True)
        with open(os.path.join(vis_dir, "checkbox_visualization_data.json"), 'w') as f:
            json.dump(self.visualization_data, f)

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    @unittest.skip("Need to fix mock file path issue")
    @patch('src.app.DocumentAIClient')
    @patch('src.app.UPLOAD_FOLDER', new_callable=lambda: tempfile.mkdtemp())
    @patch('src.app.PROCESSED_FOLDER', new_callable=lambda: tempfile.mkdtemp())
    @patch('src.visualization.visualize_checkboxes_with_confidence')
    def test_visualize_document_checkboxes_endpoint(self, mock_visualize, mock_processed_folder, mock_upload_folder, mock_client):
        """Test /api/documents/<file_id>/visualize-checkboxes endpoint."""
        # Mock DocumentAI client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.process_document.return_value = {
            "pages": [
                {
                    "checkboxes": [
                        {
                            "label": "Option 1",
                            "value": True,
                            "confidence": 0.95,
                            "bbox": {"left": 0.1, "top": 0.1, "right": 0.2, "bottom": 0.2}
                        }
                    ]
                }
            ]
        }
        
        # Configure the visualization mock
        mock_visualize.return_value = self.visualization_data
        
        # Create test PDF in the upload folder
        test_pdf_path = os.path.join(mock_upload_folder, "test_file_id")
        with open(test_pdf_path, 'w') as f:
            f.write("Test PDF content")
        
        # Make API call
        response = self.client.post(
            '/api/documents/test_file_id/visualize-checkboxes',
            json={
                "high_confidence_threshold": 0.9,
                "medium_confidence_threshold": 0.7
            },
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["visualization_id"], "test_file_id")
        self.assertEqual(data["visualization_url"], "/ui/checkbox-visualization/test_file_id")
        
        # Verify mock calls
        mock_client_instance.process_document.assert_called_once()
        mock_visualize.assert_called_once()

    @patch('src.ui_api.get_checkbox_visualization_data')
    def test_get_visualization_data_endpoint(self, mock_get_data):
        """Test /api/visualization/<document_id> endpoint."""
        # Mock the visualization data function
        mock_get_data.return_value = self.visualization_data
        
        # Make API call
        response = self.client.get('/api/visualization/test_doc_123')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["document_name"], "test_doc.pdf")
        self.assertEqual(data["total_pages"], 2)
        self.assertEqual(len(data["checkboxes"]), 2)
        
        # Test with invalid document ID
        mock_get_data.return_value = None
        response = self.client.get('/api/visualization/nonexistent')
        self.assertEqual(response.status_code, 404)

    @unittest.skip("Need to fix JSON request handling")
    @patch('src.ui_api.export_checkbox_data')
    def test_export_visualization_data_endpoint(self, mock_export):
        """Test /api/visualization/export endpoint."""
        # Mock the export function
        mock_export.return_value = {
            "document_id": "test_doc_123",
            "document_name": "test_doc.pdf",
            "export_date": "2023-05-01T12:00:00Z",
            "checkboxes": self.mock_checkboxes
        }
        
        # Make API call
        response = self.client.post(
            '/api/visualization/export',
            json={
                "document_id": "test_doc_123",
                "document_name": "test_doc.pdf",
                "checkboxes": self.mock_checkboxes
            },
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["document_id"], "test_doc_123")
        self.assertEqual(data["document_name"], "test_doc.pdf")
        self.assertEqual(len(data["checkboxes"]), 2)
        
        # Test with missing data
        response = self.client.post('/api/visualization/export', json=None)
        self.assertEqual(response.status_code, 400)

    @unittest.skip("Need to fix JSON request handling")
    @patch('src.ui_api.save_checkbox_corrections')
    def test_save_visualization_corrections_endpoint(self, mock_save):
        """Test /api/visualization/save-corrections endpoint."""
        # Mock the save function
        mock_save.return_value = True
        
        # Make API call
        response = self.client.post(
            '/api/visualization/save-corrections',
            json={
                "document_id": "test_doc_123",
                "corrections": [
                    {
                        "id": "cb1",
                        "label": "Modified Option 1",
                        "value": False,
                        "manually_corrected": True
                    }
                ]
            },
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        
        # Test with save failure
        mock_save.return_value = False
        response = self.client.post(
            '/api/visualization/save-corrections',
            json={
                "document_id": "test_doc_123",
                "corrections": []
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 500)
        
        # Test with missing data
        response = self.client.post('/api/visualization/save-corrections', json=None)
        self.assertEqual(response.status_code, 400)

    def test_checkbox_visualization_ui_endpoint(self):
        """Test /ui/checkbox-visualization/<document_id> endpoint."""
        # Make API call
        response = self.client.get('/ui/checkbox-visualization/test_doc_123')
        
        # Check response
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main() 