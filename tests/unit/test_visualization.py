"""
Unit tests for visualization functions.
"""

import os
import shutil
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from datetime import datetime

from src.visualization import (
    visualize_template,
    visualize_checkboxes_with_confidence,
    get_checkbox_visualization_data,
    export_checkbox_data,
    save_checkbox_corrections
)


class TestVisualization(unittest.TestCase):
    """Test visualization functions."""

    def setUp(self):
        """Set up test case."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        # Create mock data
        self.mock_pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(self.mock_pdf_path, 'w') as f:
            f.write("Mock PDF content")

        self.mock_template_data = {
            "fields": [
                {
                    "name": "checkbox1",
                    "type": "checkbox",
                    "page": 1,
                    "value": True,
                    "bbox": {"left": 0.1, "top": 0.1, "right": 0.2, "bottom": 0.2}
                },
                {
                    "name": "textfield1",
                    "type": "text",
                    "page": 1,
                    "value": "Sample text",
                    "bbox": {"left": 0.3, "top": 0.3, "right": 0.5, "bottom": 0.4}
                }
            ]
        }

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

    def tearDown(self):
        """Clean up after test case."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    @patch('src.visualization.convert_from_path')
    @patch('src.visualization.Image')
    @patch('src.visualization.ImageDraw')
    def test_visualize_template(self, mock_draw, mock_image, mock_convert):
        """Test template visualization function."""
        # Mock the PDF conversion
        mock_page = MagicMock()
        mock_page.size = (600, 800)
        mock_convert.return_value = [mock_page]

        # Mock the drawing
        mock_draw_instance = MagicMock()
        mock_draw.Draw.return_value = mock_draw_instance

        # Call the function
        result = visualize_template(self.mock_pdf_path, self.mock_template_data, self.output_dir)

        # Verify results
        self.assertEqual(len(result), 1)  # Should have 1 page
        self.assertTrue(mock_convert.called)
        self.assertTrue(mock_draw.Draw.called)
        self.assertTrue(mock_draw_instance.rectangle.called)
        self.assertTrue(mock_draw_instance.text.called)

    @patch('src.visualization.convert_from_path')
    @patch('src.visualization.Image')
    @patch('src.visualization.ImageDraw')
    def test_visualize_checkboxes_with_confidence(self, mock_draw, mock_image, mock_convert):
        """Test checkbox visualization with confidence function."""
        # Mock the PDF conversion
        mock_page1 = MagicMock()
        mock_page1.size = (600, 800)
        mock_page2 = MagicMock()
        mock_page2.size = (600, 800)
        mock_convert.return_value = [mock_page1, mock_page2]

        # Mock the drawing
        mock_draw_instance = MagicMock()
        mock_draw.Draw.return_value = mock_draw_instance

        # Call the function
        result = visualize_checkboxes_with_confidence(
            self.mock_pdf_path, 
            self.mock_checkboxes,
            self.output_dir,
            0.9,
            0.7
        )

        # Verify results
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(len(result["pages"]), 2)
        self.assertEqual(len(result["checkboxes"]), 3)
        
        # Check confidence categories
        checkbox_high = next(cb for cb in result["checkboxes"] if cb["id"] == "cb1")
        checkbox_medium = next(cb for cb in result["checkboxes"] if cb["id"] == "cb2")
        checkbox_low = next(cb for cb in result["checkboxes"] if cb["id"] == "cb3")
        
        self.assertEqual(checkbox_high["confidence_category"], "high")
        self.assertEqual(checkbox_medium["confidence_category"], "medium")
        self.assertEqual(checkbox_low["confidence_category"], "low")
        
        # Verify drawing calls
        self.assertTrue(mock_convert.called)
        self.assertTrue(mock_draw.Draw.called)
        self.assertTrue(mock_draw_instance.rectangle.called)
        self.assertTrue(mock_draw_instance.text.called)

    @patch('src.visualization.os.path.exists')
    @patch('src.visualization.open', new_callable=mock_open)
    @patch('src.visualization.json.load')
    def test_get_checkbox_visualization_data(self, mock_json_load, mock_file, mock_path_exists):
        """Test getting checkbox visualization data."""
        # Setup mocks
        mock_path_exists.return_value = True
        mock_json_load.return_value = {
            "document_name": "test.pdf",
            "checkboxes": self.mock_checkboxes
        }
        
        # Call the function
        result = get_checkbox_visualization_data("test_vis_id")
        
        # Verify results
        self.assertEqual(result["document_name"], "test.pdf")
        self.assertEqual(len(result["checkboxes"]), 3)
        mock_path_exists.assert_called()
        mock_file.assert_called()
        mock_json_load.assert_called()

    def test_export_checkbox_data(self):
        """Test exporting checkbox data."""
        # Prepare test data
        export_data = {
            "document_id": "doc123",
            "document_name": "test.pdf",
            "checkboxes": self.mock_checkboxes
        }
        
        # Call the function
        result = export_checkbox_data(export_data)
        
        # Verify results
        self.assertEqual(result["document_id"], "doc123")
        self.assertEqual(result["document_name"], "test.pdf")
        self.assertEqual(len(result["checkboxes"]), 3)
        self.assertIn("export_date", result)

    def test_save_checkbox_corrections(self):
        """Test saving checkbox corrections."""
        # Prepare test data
        corrections_data = {
            "document_id": "doc123",
            "corrections": [
                {
                    "id": "cb1",
                    "label": "Modified Option 1",
                    "value": False,
                    "manually_corrected": True
                }
            ]
        }
        
        # Call the function
        result = save_checkbox_corrections(corrections_data)
        
        # Verify results
        self.assertTrue(result)
        
        # Test with invalid data
        invalid_data = {"document_id": "doc123", "corrections": []}
        result = save_checkbox_corrections(invalid_data)
        self.assertFalse(result)
        
        # Test with missing document_id
        invalid_data = {"corrections": [{"id": "cb1"}]}
        result = save_checkbox_corrections(invalid_data)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main() 