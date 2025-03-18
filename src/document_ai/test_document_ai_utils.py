"""
Unit tests for the document_ai_utils module.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json
import base64
from datetime import datetime

from document_ai.document_ai_utils import (
    normalize_bounding_box,
    save_document_as_json,
    get_confidence_score,
    encode_image_for_visualization,
    generate_color_for_field,
    generate_visualization_data,
    validate_document_structure
)


class TestDocumentAIUtils(unittest.TestCase):
    """Test cases for document_ai_utils functions."""
    
    def test_validate_document_structure(self):
        """Test validate_document_structure function for various document structures."""
        # Test with valid document
        valid_doc = MagicMock()
        valid_doc.pages = [MagicMock(), MagicMock()]
        valid_doc.text = "Sample document text"
        
        is_valid, message, confidence = validate_document_structure(valid_doc)
        self.assertTrue(is_valid)
        self.assertEqual(confidence, 1.0)
        
        # Test with None document
        is_valid, message, confidence = validate_document_structure(None)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Document is None")
        self.assertEqual(confidence, 0.0)
        
        # Test with no pages
        no_pages_doc = MagicMock()
        no_pages_doc.pages = []
        
        is_valid, message, confidence = validate_document_structure(no_pages_doc)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Document has no pages")
        self.assertEqual(confidence, 0.0)
        
        # Test with no text content
        no_text_doc = MagicMock()
        no_text_doc.pages = [MagicMock(), MagicMock()]
        no_text_doc.text = ""
        
        is_valid, message, confidence = validate_document_structure(no_text_doc)
        self.assertTrue(is_valid)  # Still valid but with lower confidence
        self.assertEqual(confidence, 0.7)
        
        # Test with rotated page
        rotated_page_doc = MagicMock()
        rotated_page_doc.pages = [MagicMock()]
        rotated_page_doc.pages[0].rotation = 90
        rotated_page_doc.text = "Sample document text"
        
        is_valid, message, confidence = validate_document_structure(rotated_page_doc)
        self.assertTrue(is_valid)
        self.assertEqual(confidence, 0.8)
        
        # Test with multiple issues (no text and rotated page)
        problematic_doc = MagicMock()
        problematic_doc.pages = [MagicMock()]
        problematic_doc.pages[0].rotation = 90
        problematic_doc.text = ""
        
        is_valid, message, confidence = validate_document_structure(problematic_doc)
        self.assertTrue(is_valid)
        self.assertEqual(confidence, 0.56)  # 0.7 * 0.8
    
    def test_normalize_bounding_box(self):
        """Test normalize_bounding_box function."""
        # Test with valid bounding box
        bbox = [
            {"x": 0.1, "y": 0.1},
            {"x": 0.2, "y": 0.1},
            {"x": 0.2, "y": 0.2},
            {"x": 0.1, "y": 0.2}
        ]
        
        result = normalize_bounding_box(bbox)
        
        self.assertEqual(result["x"], 0.1)
        self.assertEqual(result["y"], 0.1)
        self.assertEqual(result["width"], 0.1)
        self.assertEqual(result["height"], 0.1)
        
        # Test with empty bounding box
        result = normalize_bounding_box([])
        
        self.assertEqual(result["x"], 0)
        self.assertEqual(result["y"], 0)
        self.assertEqual(result["width"], 0)
        self.assertEqual(result["height"], 0)
        
        # Test with None
        result = normalize_bounding_box(None)
        
        self.assertEqual(result["x"], 0)
        self.assertEqual(result["y"], 0)
        self.assertEqual(result["width"], 0)
        self.assertEqual(result["height"], 0)
    
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('datetime.datetime')
    def test_save_document_as_json(self, mock_datetime, mock_json_dump, mock_file, mock_makedirs):
        """Test save_document_as_json function."""
        # Mock the datetime.now() call
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20230101_120000"
        mock_datetime.now.return_value = mock_now
        
        # Test document data
        document_data = {"text": "test", "fields": []}
        output_path = "/test/output"
        fixed_timestamp = "20230101_120000"
        
        # Call the function with fixed timestamp
        result = save_document_as_json(document_data, output_path, fixed_timestamp)
        
        # Verify the directories were created
        mock_makedirs.assert_called_with(output_path, exist_ok=True)
        
        # Verify the file was opened for writing
        expected_path = os.path.join(output_path, "document_20230101_120000.json")
        mock_file.assert_called_with(expected_path, "w")
        
        # Verify json.dump was called with the document data
        mock_json_dump.assert_called_with(document_data, mock_file(), indent=2)
        
        # Verify the result is the expected path
        self.assertEqual(result, expected_path)
    
    def test_get_confidence_score(self):
        """Test get_confidence_score function."""
        # Test with entity having confidence
        entity = MagicMock()
        entity.confidence = 0.95
        
        result = get_confidence_score(entity)
        
        self.assertEqual(result, 0.95)
        
        # Test with entity without confidence
        entity = MagicMock(spec=[])
        
        result = get_confidence_score(entity)
        
        self.assertEqual(result, 0.0)
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'test image data')
    def test_encode_image_for_visualization(self, mock_file):
        """Test encode_image_for_visualization function."""
        # Test with JPEG image
        jpeg_path = "test.jpg"
        
        result = encode_image_for_visualization(jpeg_path)
        
        expected_data_uri = "data:image/jpeg;base64," + base64.b64encode(b'test image data').decode('utf-8')
        self.assertEqual(result, expected_data_uri)
        
        # Test with PNG image
        png_path = "test.png"
        
        result = encode_image_for_visualization(png_path)
        
        expected_data_uri = "data:image/png;base64," + base64.b64encode(b'test image data').decode('utf-8')
        self.assertEqual(result, expected_data_uri)
        
        # Test with PDF
        pdf_path = "test.pdf"
        
        result = encode_image_for_visualization(pdf_path)
        
        expected_data_uri = "data:application/pdf;base64," + base64.b64encode(b'test image data').decode('utf-8')
        self.assertEqual(result, expected_data_uri)
    
    def test_generate_color_for_field(self):
        """Test generate_color_for_field function."""
        # Test with known field types
        self.assertEqual(generate_color_for_field("checkbox"), "#FF5733")
        self.assertEqual(generate_color_for_field("text"), "#33A8FF")
        self.assertEqual(generate_color_for_field("number"), "#33FF57")
        self.assertEqual(generate_color_for_field("date"), "#FF33F5")
        
        # Test with unknown field type
        self.assertEqual(generate_color_for_field("unknown"), "#AAAAAA")
        
        # Test case insensitivity
        self.assertEqual(generate_color_for_field("CHECKBOX"), "#FF5733")
        self.assertEqual(generate_color_for_field("Text"), "#33A8FF")
    
    def test_generate_visualization_data(self):
        """Test generate_visualization_data function."""
        # Create test document data
        document_data = {
            "pages": [
                {
                    "page_number": 1,
                    "dimensions": {"width": 8.5, "height": 11.0, "unit": "inch"},
                    "fields": [
                        {
                            "id": "field_1",
                            "type": "checkbox",
                            "name": "Option 1",
                            "value": True,
                            "bbox": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.2}]
                        },
                        {
                            "id": "field_2",
                            "type": "text",
                            "name": "Name",
                            "value": "John Doe",
                            "bbox": [{"x": 0.3, "y": 0.3}, {"x": 0.4, "y": 0.4}]
                        }
                    ]
                }
            ]
        }
        
        # Call the function
        result = generate_visualization_data(document_data)
        
        # Verify the structure of the result
        self.assertEqual(len(result["pages"]), 1)
        self.assertEqual(len(result["fields"]), 2)
        
        # Verify the page data
        page_data = result["pages"][0]
        self.assertEqual(page_data["page_number"], 1)
        self.assertEqual(page_data["width"], 8.5)
        self.assertEqual(page_data["height"], 11.0)
        self.assertEqual(len(page_data["elements"]), 2)
        
        # Verify the elements
        elements = page_data["elements"]
        self.assertEqual(elements[0]["id"], "field_1")
        self.assertEqual(elements[0]["type"], "checkbox")
        self.assertEqual(elements[0]["name"], "Option 1")
        self.assertEqual(elements[0]["value"], True)
        self.assertEqual(elements[0]["color"], "#FF5733")
        
        self.assertEqual(elements[1]["id"], "field_2")
        self.assertEqual(elements[1]["type"], "text")
        self.assertEqual(elements[1]["name"], "Name")
        self.assertEqual(elements[1]["value"], "John Doe")
        self.assertEqual(elements[1]["color"], "#33A8FF")
        
        # Verify the fields
        fields = result["fields"]
        self.assertEqual(fields[0]["id"], "field_1")
        self.assertEqual(fields[0]["page"], 1)
        self.assertEqual(fields[0]["name"], "Option 1")
        self.assertEqual(fields[0]["type"], "checkbox")
        self.assertEqual(fields[0]["value"], True)
        
        self.assertEqual(fields[1]["id"], "field_2")
        self.assertEqual(fields[1]["page"], 1)
        self.assertEqual(fields[1]["name"], "Name")
        self.assertEqual(fields[1]["type"], "text")
        self.assertEqual(fields[1]["value"], "John Doe")


if __name__ == '__main__':
    unittest.main() 