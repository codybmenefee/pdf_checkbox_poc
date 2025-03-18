"""
Test cases for the PDF Checkbox Extraction & Form Filling System.
"""

import os
import unittest
import json
import tempfile
from unittest.mock import patch, MagicMock
from google.cloud import documentai_v1 as documentai

from app import app
from document_ai_client import DocumentAIClient
from pdf_handler import PDFHandler
from template_manager import TemplateManager
from form_filler import FormFiller, FieldMapper
from database import DatabaseManager, TemplateModel, FilledFormModel

class TestPDFCheckboxExtraction(unittest.TestCase):
    """Test cases for PDF checkbox extraction functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create a temporary test PDF
        self.test_pdf_path = os.path.join(tempfile.gettempdir(), "test.pdf")
        with open(self.test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Count 1/Kids[3 0 R]>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    @patch('app.os.path')
    @patch('app.os')
    @patch('app.pdf_handler')
    def test_pdf_upload_and_process(self, mock_pdf_handler, mock_os, mock_os_path):
        """Test PDF upload and processing."""
        # Set up file mocks
        file_id = "test-file-id"
        filename = f"{file_id}_test.pdf"
        mock_os.listdir.return_value = [filename]
        mock_os_path.join.return_value = self.test_pdf_path
        mock_os_path.getsize.return_value = 1000
        
        # Set up the mock response for upload_pdf
        mock_pdf_handler.upload_pdf.return_value = {
            "file_id": file_id,
            "original_filename": "test.pdf",
            "stored_filename": filename,
            "file_path": self.test_pdf_path,
            "file_size": 1000
        }
        
        # Set up the mock response for process_pdf
        mock_pdf_handler.process_pdf.return_value = {
            "document_data": {
                "text": "Test document",
                "pages": [
                    {
                        "page_number": 1,
                        "dimensions": {
                            "width": 612,
                            "height": 792,
                            "unit": "PT"
                        },
                        "checkboxes": [
                            {
                                "is_checked": True,
                                "confidence": 0.95,
                                "bounding_box": [
                                    {"x": 100, "y": 100},
                                    {"x": 120, "y": 100},
                                    {"x": 120, "y": 120},
                                    {"x": 100, "y": 120}
                                ],
                                "normalized_bounding_box": [
                                    {"x": 0.1, "y": 0.1},
                                    {"x": 0.12, "y": 0.1},
                                    {"x": 0.12, "y": 0.12},
                                    {"x": 0.1, "y": 0.12}
                                ]
                            }
                        ],
                        "form_fields": [
                            {
                                "is_checkbox": True,
                                "name": "Checkbox 1",
                                "is_checked": True,
                                "value_confidence": 0.95,
                                "value_bounding_box": [
                                    {"x": 100, "y": 100},
                                    {"x": 120, "y": 100},
                                    {"x": 120, "y": 120},
                                    {"x": 100, "y": 120}
                                ]
                            }
                        ]
                    }
                ],
                "mime_type": "application/pdf"
            }
        }
        
        # Set up mock for extract_checkboxes
        mock_pdf_handler.extract_checkboxes.return_value = [
            {
                "is_checked": True,
                "confidence": 0.95,
                "bounding_box": [
                    {"x": 100, "y": 100},
                    {"x": 120, "y": 100},
                    {"x": 120, "y": 120},
                    {"x": 100, "y": 120}
                ],
                "normalized_bounding_box": [
                    {"x": 0.1, "y": 0.1},
                    {"x": 0.12, "y": 0.1},
                    {"x": 0.12, "y": 0.12},
                    {"x": 0.1, "y": 0.12}
                ]
            }
        ]
        
        # Test file upload
        with open(self.test_pdf_path, "rb") as pdf:
            response = self.app.post(
                '/api/documents/upload',
                data={'file': (pdf, 'test.pdf')},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('file_info', data)
            self.assertIn('file_id', data['file_info'])
            
            file_id = data['file_info']['file_id']
            
            # Test document processing
            response = self.app.post(f'/api/documents/{file_id}/process')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('checkboxes', data)
            self.assertEqual(len(data['checkboxes']), 1)
            self.assertTrue(data['checkboxes'][0]['is_checked'])

class TestTemplateManagement(unittest.TestCase):
    """Test cases for template management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Mock template data
        self.template_data = {
            "template_id": "test-template-id",
            "name": "Test Template",
            "description": "Template for testing",
            "created_at": "2025-03-17T18:00:00Z",
            "updated_at": "2025-03-17T18:00:00Z",
            "tags": ["test", "sample"],
            "version": 1,
            "fields": [
                {
                    "field_id": "field_1",
                    "field_type": "checkbox",
                    "label": "Checkbox 1",
                    "page": 1,
                    "coordinates": {
                        "vertices": [
                            {"x": 100, "y": 100},
                            {"x": 120, "y": 100},
                            {"x": 120, "y": 120},
                            {"x": 100, "y": 120}
                        ],
                        "normalized_vertices": [
                            {"x": 0.1, "y": 0.1},
                            {"x": 0.12, "y": 0.1},
                            {"x": 0.12, "y": 0.12},
                            {"x": 0.1, "y": 0.12}
                        ]
                    },
                    "default_value": True,
                    "confidence": 0.95
                }
            ]
        }
    
    @patch.object(TemplateManager, 'get_template')
    @patch.object(TemplateManager, 'list_templates')
    def test_template_listing_and_retrieval(self, mock_list_templates, mock_get_template):
        """Test template listing and retrieval."""
        # Mock template listing
        mock_list_templates.return_value = [self.template_data]
        
        # Test template listing
        response = self.app.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('templates', data)
        self.assertEqual(len(data['templates']), 1)
        self.assertEqual(data['templates'][0]['template_id'], 'test-template-id')
        
        # Mock template retrieval
        mock_get_template.return_value = self.template_data
        
        # Test template retrieval
        response = self.app.get('/api/templates/test-template-id')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('template', data)
        self.assertEqual(data['template']['template_id'], 'test-template-id')
        self.assertEqual(len(data['template']['fields']), 1)

class TestFormFilling(unittest.TestCase):
    """Test cases for form filling functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create a temporary test PDF
        self.test_pdf_path = os.path.join(tempfile.gettempdir(), "test.pdf")
        with open(self.test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Count 1/Kids[3 0 R]>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")
        
        # Mock template data
        self.template_data = {
            "template_id": "test-template-id",
            "name": "Test Template",
            "description": "Template for testing",
            "created_at": "2025-03-17T18:00:00Z",
            "updated_at": "2025-03-17T18:00:00Z",
            "tags": ["test", "sample"],
            "version": 1,
            "fields": [
                {
                    "field_id": "field_1",
                    "field_type": "checkbox",
                    "label": "Checkbox 1",
                    "page": 1,
                    "coordinates": {
                        "vertices": [
                            {"x": 100, "y": 100},
                            {"x": 120, "y": 100},
                            {"x": 120, "y": 120},
                            {"x": 100, "y": 120}
                        ],
                        "normalized_vertices": [
                            {"x": 0.1, "y": 0.1},
                            {"x": 0.12, "y": 0.1},
                            {"x": 0.12, "y": 0.12},
                            {"x": 0.1, "y": 0.12}
                        ]
                    },
                    "default_value": True,
                    "confidence": 0.95
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    @patch.object(TemplateModel, 'get')
    @patch.object(FormFiller, 'apply_template')
    @patch.object(FilledFormModel, 'create')
    def test_form_filling(self, mock_create_form, mock_apply_template, mock_get_template):
        """Test form filling functionality."""
        # Mock template retrieval
        mock_get_template.return_value = self.template_data
        
        # Mock template application
        filled_pdf_path = os.path.join(tempfile.gettempdir(), "filled.pdf")
        mock_apply_template.return_value = filled_pdf_path
        
        # Mock form creation
        mock_create_form.return_value = {
            "form_id": "test-form-id",
            "template_id": "test-template-id",
            "name": "Test Form",
            "created_at": "2025-03-17T18:00:00Z",
            "status": "draft",
            "document": {
                "original_filename": "test.pdf",
                "file_size": 1000,
                "filled_path": filled_pdf_path
            },
            "field_values": [
                {
                    "field_id": "field_1",
                    "value": True
                }
            ],
            "export_history": []
        }
        
        # Test form filling
        with open(self.test_pdf_path, "rb") as pdf:
            # First upload the PDF
            response = self.app.post(
                '/api/documents/upload',
                data={'file': (pdf, 'test.pdf')},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            file_id = data['file_info']['file_id']
            
            # Then fill the form
            response = self.app.post(
                '/api/forms/fill',
                json={
                    "template_id": "test-template-id",
                    "pdf_file_id": file_id,
                    "name": "Test Form",
                    "field_values": [
                        {
                            "field_id": "field_1",
                            "value": True
                        }
                    ]
                }
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('form_id', data)
            self.assertEqual(data['form_id'], 'test-form-id')

class TestExportFunctionality(unittest.TestCase):
    """Test cases for export functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_onespan_export(self):
        """Test OneSpan export functionality."""
        response = self.app.post(
            '/api/export/onespan',
            json={
                "form_id": "test-form-id"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('export_record', data)
        self.assertEqual(data['export_record']['destination'], 'OneSpan')
        self.assertEqual(data['export_record']['status'], 'success')
    
    def test_docusign_export(self):
        """Test DocuSign export functionality."""
        response = self.app.post(
            '/api/export/docusign',
            json={
                "form_id": "test-form-id"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('export_record', data)
        self.assertEqual(data['export_record']['destination'], 'DocuSign')
        self.assertEqual(data['export_record']['status'], 'success')

if __name__ == '__main__':
    unittest.main()
