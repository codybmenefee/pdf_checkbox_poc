"""
Unit tests for the document_ai_models module.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json

from google.cloud import documentai_v1 as documentai

from document_ai.document_ai_core import DocumentAIManager
from document_ai.document_ai_models import DocumentModel


class TestDocumentModel(unittest.TestCase):
    """Test cases for DocumentModel class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock Document AI manager
        self.mock_doc_ai_manager = MagicMock(spec=DocumentAIManager)
        
        # Create test instance with the mock manager
        self.document_model = DocumentModel(self.mock_doc_ai_manager)
    
    def test_init(self):
        """Test initialization of DocumentModel."""
        # Create a fresh instance
        doc_ai_manager = MagicMock(spec=DocumentAIManager)
        document_model = DocumentModel(doc_ai_manager)
        
        # Verify the manager is set properly
        self.assertEqual(document_model.doc_ai_manager, doc_ai_manager)
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'test file content')
    def test_process_file(self, mock_file):
        """Test process_file method."""
        # Mock the document AI manager's process_document method
        mock_document = MagicMock(spec=documentai.Document)
        self.mock_doc_ai_manager.process_document.return_value = mock_document
        
        # Mock the extract_document_data method
        mock_extracted_data = {'text': 'test', 'fields': []}
        self.document_model._extract_document_data = MagicMock(return_value=mock_extracted_data)
        
        # Execute the method under test
        result = self.document_model.process_file('test.pdf')
        
        # Verify the file was opened
        mock_file.assert_called_with('test.pdf', 'rb')
        
        # Verify the document manager was called with the file content
        self.mock_doc_ai_manager.process_document.assert_called_with(b'test file content')
        
        # Verify _extract_document_data was called with the document
        self.document_model._extract_document_data.assert_called_with(mock_document)
        
        # Verify the result is the mock extracted data
        self.assertEqual(result, mock_extracted_data)
    
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_process_file_not_found(self, mock_file):
        """Test process_file with file not found error."""
        # Attempt to process a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.document_model.process_file('nonexistent.pdf')
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'test file content')
    def test_process_file_with_error(self, mock_file):
        """Test process_file with processing error."""
        # Mock the document AI manager to raise an exception
        self.mock_doc_ai_manager.process_document.side_effect = Exception("Processing error")
        
        # Attempt to process a file with error
        with self.assertRaises(Exception):
            self.document_model.process_file('test.pdf')
    
    def test_process_file_with_malformed_document(self):
        """Test processing a malformed document."""
        # Set up mocks
        mock_file_content = b'malformed pdf content'
        mock_file = mock_open(read_data=mock_file_content)
        
        # Set up document with structural issues
        mock_document = MagicMock()
        mock_document.pages = []  # Empty pages list
        mock_document.text = ''   # No text
        
        # Configure mock manager to return malformed document
        self.mock_doc_ai_manager.process_document.return_value = mock_document
        
        # Execute method with mocked file operations
        with patch('builtins.open', mock_file):
            result = self.document_model.process_file('malformed.pdf')
        
        # Check that validation detected the structural issues
        self.assertIn('document_validation', result)
        self.assertFalse(result['document_validation']['is_valid'])
        self.assertEqual(result['document_validation']['error_message'], 'Document has no pages')
        self.assertEqual(result['document_validation']['confidence'], 0.0)
        
        # Check that basic structure is still returned
        self.assertIn('text', result)
        self.assertIn('pages', result)
        self.assertIn('fields', result)
        self.assertIn('checkboxes', result)
    
    def test_overlapping_form_elements(self):
        """Test detection of overlapping form elements."""
        # Create a mock page
        mock_page = MagicMock()
        
        # Create two checkboxes with overlapping bounding boxes
        # Checkbox 1
        mock_symbol1 = MagicMock()
        mock_symbol1.symbol_type = "checkbox"
        mock_symbol1.state = "checked"
        
        vertex1_1 = MagicMock()
        vertex1_1.x = 0.1
        vertex1_1.y = 0.1
        
        vertex1_2 = MagicMock()
        vertex1_2.x = 0.2
        vertex1_2.y = 0.1
        
        vertex1_3 = MagicMock()
        vertex1_3.x = 0.2
        vertex1_3.y = 0.2
        
        vertex1_4 = MagicMock()
        vertex1_4.x = 0.1
        vertex1_4.y = 0.2
        
        mock_symbol1.bounding_poly.normalized_vertices = [vertex1_1, vertex1_2, vertex1_3, vertex1_4]
        
        # Checkbox 2 (overlapping with checkbox 1)
        mock_symbol2 = MagicMock()
        mock_symbol2.symbol_type = "checkbox"
        mock_symbol2.state = "unchecked"
        
        vertex2_1 = MagicMock()
        vertex2_1.x = 0.15
        vertex2_1.y = 0.15
        
        vertex2_2 = MagicMock()
        vertex2_2.x = 0.25
        vertex2_2.y = 0.15
        
        vertex2_3 = MagicMock()
        vertex2_3.x = 0.25
        vertex2_3.y = 0.25
        
        vertex2_4 = MagicMock()
        vertex2_4.x = 0.15
        vertex2_4.y = 0.25
        
        mock_symbol2.bounding_poly.normalized_vertices = [vertex2_1, vertex2_2, vertex2_3, vertex2_4]
        
        # Set up paragraph that overlaps with both checkboxes
        mock_paragraph = MagicMock()
        p_vertex1 = MagicMock()
        p_vertex1.x = 0.18
        p_vertex1.y = 0.18
        
        p_vertex2 = MagicMock()
        p_vertex2.x = 0.3
        p_vertex2.y = 0.18
        
        p_vertex3 = MagicMock()
        p_vertex3.x = 0.3
        p_vertex3.y = 0.3
        
        p_vertex4 = MagicMock()
        p_vertex4.x = 0.18
        p_vertex4.y = 0.3
        
        mock_paragraph.bounding_poly.normalized_vertices = [p_vertex1, p_vertex2, p_vertex3, p_vertex4]
        
        mock_page.detected_symbols = [mock_symbol1, mock_symbol2]
        mock_page.paragraphs = [mock_paragraph]
        
        # Mock the _find_checkbox_label method to return a label for both
        self.document_model._find_checkbox_label = MagicMock()
        self.document_model._find_checkbox_label.side_effect = [
            ("Overlapping label", 0.7),
            ("Another overlapping label", 0.6)
        ]
        
        # Execute the method under test
        result = self.document_model._extract_checkboxes(mock_page, "Test text")
        
        # Check that both checkboxes are detected despite overlap
        self.assertEqual(len(result), 2)
        
        # Check that confidence scores reflect the overlap
        self.assertTrue(result[0]["confidence_score"] <= 0.7)
        self.assertTrue(result[1]["confidence_score"] <= 0.6)
    
    def test_extract_document_data(self):
        """Test _extract_document_data method."""
        # Create a mock document with minimal structure
        mock_document = MagicMock(spec=documentai.Document)
        mock_document.text = "Test document text"
        mock_document.mime_type = "application/pdf"
        
        # Mock the pages
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_document.pages = [mock_page1, mock_page2]
        
        # Mock page dimension properties
        mock_page1.dimension = MagicMock()
        mock_page1.dimension.width = 8.5
        mock_page1.dimension.height = 11.0
        mock_page1.dimension.unit = "inch"
        
        # Mock form fields extraction
        mock_fields1 = [
            {"name": "Field1", "value": "Value1", "type": "text", "is_checkbox": False, "bbox": []}
        ]
        mock_fields2 = [
            {"name": "Field2", "value": True, "type": "checkbox", "is_checkbox": True, "bbox": []}
        ]
        
        # Mock checkboxes extraction
        mock_checkboxes1 = [
            {"symbol_type": "checkbox", "is_checked": True, "label": "Checkbox1", "normalized_bounding_box": []}
        ]
        mock_checkboxes2 = []
        
        # Set up mocks for the extraction methods
        self.document_model._extract_form_fields = MagicMock()
        self.document_model._extract_form_fields.side_effect = [mock_fields1, mock_fields2]
        
        self.document_model._extract_checkboxes = MagicMock()
        self.document_model._extract_checkboxes.side_effect = [mock_checkboxes1, mock_checkboxes2]
        
        # Execute the method under test
        result = self.document_model._extract_document_data(mock_document)
        
        # Verify the extraction methods were called
        self.assertEqual(self.document_model._extract_form_fields.call_count, 2)
        self.assertEqual(self.document_model._extract_checkboxes.call_count, 2)
        
        # Verify the structure of the result
        self.assertEqual(result["text"], "Test document text")
        self.assertEqual(result["mime_type"], "application/pdf")
        self.assertEqual(len(result["pages"]), 2)
        
        # Verify fields were added to the result
        self.assertGreaterEqual(len(result["fields"]), 2)
        
        # Verify page data structure
        page1_data = result["pages"][0]
        self.assertEqual(page1_data["dimensions"]["width"], 8.5)
        self.assertEqual(page1_data["dimensions"]["height"], 11.0)
        self.assertEqual(page1_data["dimensions"]["unit"], "inch")
    
    def test_extract_form_fields(self):
        """Test _extract_form_fields method."""
        # Create a mock page
        mock_page = MagicMock()
        
        # Create mock form fields
        mock_field1 = MagicMock()
        mock_field1.field_name = MagicMock()
        mock_field1.field_value = MagicMock()
        
        mock_field2 = MagicMock()
        mock_field2.field_name = MagicMock()
        mock_field2.field_value = MagicMock()
        mock_field2.field_value.value_type = "boolean"
        
        mock_page.form_fields = [mock_field1, mock_field2]
        
        # Mock the _get_text_from_layout method
        self.document_model._get_text_from_layout = MagicMock()
        self.document_model._get_text_from_layout.side_effect = [
            "Name1", "Value1", "Name2", "true"
        ]
        
        # Execute the method under test
        result = self.document_model._extract_form_fields(mock_page, "Test text")
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Name1")
        self.assertEqual(result[0]["value"], "Value1")
        self.assertEqual(result[0]["type"], "text")
        self.assertFalse(result[0]["is_checkbox"])
        
        self.assertEqual(result[1]["name"], "Name2")
        self.assertEqual(result[1]["value"], True)
        self.assertEqual(result[1]["type"], "checkbox")
        self.assertTrue(result[1]["is_checkbox"])
    
    def test_extract_checkboxes(self):
        """Test _extract_checkboxes method."""
        # Create a mock page
        mock_page = MagicMock()
        
        # Create mock symbols
        mock_symbol1 = MagicMock()
        mock_symbol1.symbol_type = "checkbox"
        mock_symbol1.state = "checked"
        
        mock_symbol2 = MagicMock()
        mock_symbol2.symbol_type = "checkbox"
        mock_symbol2.state = "unchecked"
        
        mock_symbol3 = MagicMock()
        mock_symbol3.symbol_type = "other"
        
        # Create a mock non-standard "square" checkbox
        mock_symbol4 = MagicMock()
        mock_symbol4.symbol_type = "square"
        mock_symbol4.state = "checked"
        
        # Create a mock unknown symbol that looks like a checkbox
        mock_symbol5 = MagicMock()
        mock_symbol5.symbol_type = "unknown"
        
        # Set up bounding polygon for the unknown symbol to be square-shaped
        vertex1 = MagicMock()
        vertex1.x = 0.5
        vertex1.y = 0.5
        
        vertex2 = MagicMock()
        vertex2.x = 0.55
        vertex2.y = 0.5
        
        vertex3 = MagicMock()
        vertex3.x = 0.55
        vertex3.y = 0.55
        
        vertex4 = MagicMock()
        vertex4.x = 0.5
        vertex4.y = 0.55
        
        mock_symbol5.bounding_poly.normalized_vertices = [vertex1, vertex2, vertex3, vertex4]
        
        # Create a rotated checkbox
        mock_symbol6 = MagicMock()
        mock_symbol6.symbol_type = "checkbox"
        mock_symbol6.state = "unchecked"
        
        # Set up a rotated bounding polygon
        r_vertex1 = MagicMock()
        r_vertex1.x = 0.7
        r_vertex1.y = 0.3
        
        r_vertex2 = MagicMock()
        r_vertex2.x = 0.8
        r_vertex2.y = 0.4
        
        r_vertex3 = MagicMock()
        r_vertex3.x = 0.7
        r_vertex3.y = 0.5
        
        r_vertex4 = MagicMock()
        r_vertex4.x = 0.6
        r_vertex4.y = 0.4
        
        mock_symbol6.bounding_poly.normalized_vertices = [r_vertex1, r_vertex2, r_vertex3, r_vertex4]
        
        # Add all symbols to the page
        mock_page.detected_symbols = [mock_symbol1, mock_symbol2, mock_symbol3, mock_symbol4, mock_symbol5, mock_symbol6]
        
        # Mock the _find_checkbox_label method
        self.document_model._find_checkbox_label = MagicMock()
        self.document_model._find_checkbox_label.side_effect = [
            ("Label1", 1.0),
            ("Label2", 0.9),
            (None, 0.0),
            ("Non-standard checkbox", 0.8),
            ("Inferred checkbox", 0.7),
            ("Rotated checkbox", 0.9)
        ]
        
        # Execute the method under test
        result = self.document_model._extract_checkboxes(mock_page, "Test text")
        
        # Verify the result
        self.assertEqual(len(result), 5)  # All checkbox-like symbols
        
        # Standard checkbox checked
        self.assertEqual(result[0]["symbol_type"], "checkbox")
        self.assertTrue(result[0]["is_checked"])
        self.assertEqual(result[0]["label"], "Label1")
        self.assertEqual(result[0]["confidence_score"], 1.0)
        
        # Standard checkbox unchecked
        self.assertEqual(result[1]["symbol_type"], "checkbox")
        self.assertFalse(result[1]["is_checked"])
        self.assertEqual(result[1]["label"], "Label2")
        self.assertEqual(result[1]["confidence_score"], 0.9)
        
        # Non-standard square checkbox
        self.assertEqual(result[2]["symbol_type"], "square")
        self.assertTrue(result[2]["is_checked"])
        self.assertEqual(result[2]["label"], "Non-standard checkbox")
        self.assertEqual(result[2]["confidence_score"], 0.8)
        
        # Inferred checkbox from unknown symbol with square shape
        self.assertEqual(result[3]["symbol_type"], "inferred_checkbox")
        self.assertIn("confidence_score", result[3])
        self.assertTrue(result[3]["confidence_score"] < 1.0)  # Lower confidence for inferred
        
        # Rotated checkbox
        self.assertEqual(result[4]["symbol_type"], "checkbox")
        self.assertFalse(result[4]["is_checked"])
        self.assertEqual(result[4]["label"], "Rotated checkbox")
        self.assertTrue(result[4]["confidence_score"] < 1.0)  # Lower confidence for rotated
    
    def test_extract_checkboxes_with_errors(self):
        """Test _extract_checkboxes method with errors."""
        # Test with page having no detected_symbols attribute
        mock_page_no_symbols = MagicMock()
        # Remove detected_symbols attribute
        delattr(mock_page_no_symbols, 'detected_symbols')
        
        result = self.document_model._extract_checkboxes(mock_page_no_symbols, "Test text")
        self.assertEqual(result, [])
        
        # Test with exception during processing
        mock_page = MagicMock()
        mock_page.detected_symbols = [MagicMock()]
        
        # Mock to raise exception
        self.document_model._find_checkbox_label = MagicMock(side_effect=Exception("Test error"))
        
        result = self.document_model._extract_checkboxes(mock_page, "Test text")
        self.assertEqual(result, [])
    
    def test_get_text_from_layout(self):
        """Test _get_text_from_layout method."""
        # Create a mock layout
        mock_layout = MagicMock()
        mock_layout.text_anchor = MagicMock()
        
        # Create mock text segments
        segment1 = MagicMock()
        segment1.start_index = 0
        segment1.end_index = 5
        
        segment2 = MagicMock()
        segment2.start_index = 10
        segment2.end_index = 15
        
        mock_layout.text_anchor.text_segments = [segment1, segment2]
        
        # Test text
        test_text = "Hello world, this is a test."
        
        # Execute the method under test
        result = self.document_model._get_text_from_layout(mock_layout, test_text)
        
        # Verify the result
        self.assertEqual(result, "Hello world")
    
    def test_find_checkbox_label(self):
        """Test _find_checkbox_label method."""
        # Create a mock page with paragraphs
        mock_page = MagicMock()
        mock_page.page_number = 1
        
        # Create a mock checkbox symbol with bounding poly
        mock_symbol = MagicMock()
        vertex1 = MagicMock()
        vertex1.x = 0.1
        vertex1.y = 0.1
        
        vertex2 = MagicMock()
        vertex2.x = 0.2
        vertex2.y = 0.1
        
        vertex3 = MagicMock()
        vertex3.x = 0.2
        vertex3.y = 0.2
        
        vertex4 = MagicMock()
        vertex4.x = 0.1
        vertex4.y = 0.2
        
        mock_symbol.bounding_poly.normalized_vertices = [vertex1, vertex2, vertex3, vertex4]
        
        # Create a mock paragraph near the checkbox
        mock_paragraph_close = MagicMock()
        p_vertex1 = MagicMock()
        p_vertex1.x = 0.25
        p_vertex1.y = 0.15
        
        p_vertex2 = MagicMock()
        p_vertex2.x = 0.4
        p_vertex2.y = 0.15
        
        p_vertex3 = MagicMock()
        p_vertex3.x = 0.4
        p_vertex3.y = 0.25
        
        p_vertex4 = MagicMock()
        p_vertex4.x = 0.25
        p_vertex4.y = 0.25
        
        mock_paragraph_close.bounding_poly.normalized_vertices = [p_vertex1, p_vertex2, p_vertex3, p_vertex4]
        
        # Test case 1: Normal case with nearby text
        mock_page.paragraphs = [mock_paragraph_close]
        self.document_model._get_text_from_layout = MagicMock(return_value="Checkbox Label")
        
        result, confidence = self.document_model._find_checkbox_label(mock_page, mock_symbol, "Test text")
        
        # Verify the result
        self.assertEqual(result, "Checkbox Label")
        self.assertTrue(confidence > 0.9)  # High confidence for close text
        
        # Test case 2: No nearby text (no paragraphs)
        mock_page.paragraphs = []
        
        result, confidence = self.document_model._find_checkbox_label(mock_page, mock_symbol, "Test text")
        
        # Verify fallback behavior
        self.assertTrue("Checkbox at" in result)
        self.assertTrue("Page 1" in result)
        self.assertEqual(confidence, 0.2)  # Low confidence for fallback
        
        # Test case 3: Text is too far away
        mock_paragraph_far = MagicMock()
        pf_vertex1 = MagicMock()
        pf_vertex1.x = 0.8
        pf_vertex1.y = 0.8
        
        pf_vertex2 = MagicMock()
        pf_vertex2.x = 0.9
        pf_vertex2.y = 0.8
        
        pf_vertex3 = MagicMock()
        pf_vertex3.x = 0.9
        pf_vertex3.y = 0.9
        
        pf_vertex4 = MagicMock()
        pf_vertex4.x = 0.8
        pf_vertex4.y = 0.9
        
        mock_paragraph_far.bounding_poly.normalized_vertices = [pf_vertex1, pf_vertex2, pf_vertex3, pf_vertex4]
        
        mock_page.paragraphs = [mock_paragraph_far]
        self.document_model._get_text_from_layout = MagicMock(return_value="Far away text")
        
        result, confidence = self.document_model._find_checkbox_label(mock_page, mock_symbol, "Test text")
        
        # Verify fallback behavior
        self.assertTrue("Checkbox at" in result)
        self.assertTrue("Page 1" in result)
        self.assertEqual(confidence, 0.2)
        
        # Test case 4: RTL (right-to-left) layout
        mock_paragraph_rtl = MagicMock()
        rtl_vertex1 = MagicMock()
        rtl_vertex1.x = 0.0
        rtl_vertex1.y = 0.15
        
        rtl_vertex2 = MagicMock()
        rtl_vertex2.x = 0.09
        rtl_vertex2.y = 0.15
        
        rtl_vertex3 = MagicMock()
        rtl_vertex3.x = 0.09
        rtl_vertex3.y = 0.25
        
        rtl_vertex4 = MagicMock()
        rtl_vertex4.x = 0.0
        rtl_vertex4.y = 0.25
        
        mock_paragraph_rtl.bounding_poly.normalized_vertices = [rtl_vertex1, rtl_vertex2, rtl_vertex3, rtl_vertex4]
        
        # Add both paragraphs to test which one is chosen
        mock_page.paragraphs = [mock_paragraph_close, mock_paragraph_rtl]
        
        # Label to the right should be chosen with higher confidence in default LTR
        self.document_model._get_text_from_layout = MagicMock()
        self.document_model._get_text_from_layout.side_effect = ["Right label", "Left label"]
        
        result, confidence = self.document_model._find_checkbox_label(mock_page, mock_symbol, "Test text")
        
        # Verify the right label is chosen with higher confidence
        self.assertEqual(result, "Right label")
        
        # Test case 5: Vertical layout text (below the checkbox)
        mock_paragraph_below = MagicMock()
        below_vertex1 = MagicMock()
        below_vertex1.x = 0.15
        below_vertex1.y = 0.25
        
        below_vertex2 = MagicMock()
        below_vertex2.x = 0.25
        below_vertex2.y = 0.25
        
        below_vertex3 = MagicMock()
        below_vertex3.x = 0.25
        below_vertex3.y = 0.35
        
        below_vertex4 = MagicMock()
        below_vertex4.x = 0.15
        below_vertex4.y = 0.35
        
        mock_paragraph_below.bounding_poly.normalized_vertices = [
            below_vertex1, below_vertex2, below_vertex3, below_vertex4
        ]
        
        mock_page.paragraphs = [mock_paragraph_below]
        self.document_model._get_text_from_layout = MagicMock(return_value="Text below checkbox")
        
        result, confidence = self.document_model._find_checkbox_label(mock_page, mock_symbol, "Test text")
        
        # Verify the text below is found
        self.assertEqual(result, "Text below checkbox")
        self.assertTrue(confidence > 0.5)  # Decent confidence for text below


if __name__ == '__main__':
    unittest.main() 