"""
Unit tests for the document_ai_core module.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile

from google.cloud import documentai_v1 as documentai

from document_ai.document_ai_core import DocumentAIManager


class TestDocumentAIManager(unittest.TestCase):
    """Test cases for DocumentAIManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test instance in test mode
        self.doc_ai_manager = DocumentAIManager(
            project_id='test-project', 
            location='us',
            processor_id='test-processor',
            test_mode=True
        )
    
    def test_init(self):
        """Test initialization of DocumentAIManager."""
        # Test initialization with test_mode
        doc_ai_manager = DocumentAIManager(
            project_id='custom-project',
            location='custom-location',
            processor_id='custom-processor',
            test_mode=True
        )
        
        # Verify the parameters are set properly
        self.assertEqual(doc_ai_manager.project_id, 'custom-project')
        self.assertEqual(doc_ai_manager.location, 'custom-location')
        self.assertEqual(doc_ai_manager.processor_id, 'custom-processor')
        self.assertIsNone(doc_ai_manager.client)
        self.assertEqual(
            doc_ai_manager.processor_name, 
            'projects/custom-project/locations/custom-location/processors/custom-processor'
        )
    
    def test_test_mode(self):
        """Test initialization in test mode."""
        # Create manager in test mode
        doc_ai_manager = DocumentAIManager(
            project_id='test-project',
            location='us',
            processor_id='test-processor',
            test_mode=True
        )
        
        # Verify attributes
        self.assertIsNone(doc_ai_manager.client)
        self.assertEqual(doc_ai_manager.project_id, 'test-project')
        self.assertEqual(doc_ai_manager.location, 'us')
        self.assertEqual(doc_ai_manager.processor_id, 'test-processor')
    
    @patch('google.cloud.documentai_v1.DocumentProcessorServiceClient')
    def test_init_with_client(self, mock_client_class):
        """Test initialization with actual client creation."""
        # Configure the mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.processor_path.return_value = 'mocked-processor-path'
        
        # Create manager with client (test_mode=False)
        doc_ai_manager = DocumentAIManager(
            project_id='real-project',
            location='us',
            processor_id='real-processor',
            test_mode=False
        )
        
        # Verify the client was created
        mock_client_class.assert_called_once()
        self.assertIsNotNone(doc_ai_manager.client)
        
        # Verify processor_path was called with correct arguments
        mock_client.processor_path.assert_called_with('real-project', 'us', 'real-processor')
        self.assertEqual(doc_ai_manager.processor_name, 'mocked-processor-path')
    
    @patch('google.cloud.documentai_v1.DocumentProcessorServiceClient')
    def test_init_with_error(self, mock_client_class):
        """Test error handling during initialization."""
        # Configure the mock to raise an exception
        mock_client_class.side_effect = Exception("Connection error")
        
        # Attempt to create a manager with client (test_mode=False)
        with self.assertRaises(Exception):
            DocumentAIManager(
                project_id='error-project',
                location='us',
                processor_id='error-processor',
                test_mode=False
            )
    
    def test_process_document_in_test_mode(self):
        """Test process_document method in test mode."""
        # Execute in test mode
        result = self.doc_ai_manager.process_document(b'test content')
        
        # Should return None in test mode
        self.assertIsNone(result)
    
    @patch('google.cloud.documentai_v1.DocumentProcessorServiceClient')
    def test_process_document(self, mock_client_class):
        """Test process_document method."""
        # Configure the mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.processor_path.return_value = 'mocked-processor-path'
        
        # Configure the process_document response
        mock_document = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_document
        mock_client.process_document.return_value = mock_result
        
        # Create manager with mocked client
        doc_ai_manager = DocumentAIManager(
            project_id='test-project',
            location='us',
            processor_id='test-processor',
            test_mode=False
        )
        
        # Execute the method under test
        result = doc_ai_manager.process_document(b'test content', 'test/mime')
        
        # Verify the client's process_document method was called
        mock_client.process_document.assert_called_once()
        
        # Verify the request was correctly constructed
        request_arg = mock_client.process_document.call_args[1]['request']
        self.assertEqual(request_arg.name, 'mocked-processor-path')
        self.assertEqual(request_arg.raw_document.content, b'test content')
        self.assertEqual(request_arg.raw_document.mime_type, 'test/mime')
        
        # Verify the result is the mocked document
        self.assertEqual(result, mock_document)
    
    @patch('google.cloud.documentai_v1.DocumentProcessorServiceClient')
    def test_process_document_with_error(self, mock_client_class):
        """Test error handling in process_document method."""
        # Configure the mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.processor_path.return_value = 'mocked-processor-path'
        
        # Configure the process_document method to raise an exception
        mock_client.process_document.side_effect = Exception("Processing error")
        
        # Create manager with mocked client
        doc_ai_manager = DocumentAIManager(
            project_id='test-project',
            location='us',
            processor_id='test-processor',
            test_mode=False
        )
        
        # Attempt to process a document
        with self.assertRaises(Exception):
            doc_ai_manager.process_document(b'test content')


if __name__ == '__main__':
    unittest.main() 