"""
Adapter for backward compatibility with the original document_ai_client.py.
This module provides a DocumentAIClient class that maintains the same interface
but uses the refactored Document AI components under the hood.
"""

import logging
from typing import Dict, List, Any, Optional

from src.document_ai.document_ai_core import DocumentAIManager
from src.document_ai.document_ai_models import DocumentModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentAIClient:
    """
    Adapter for backward compatibility with the original DocumentAIClient.
    This class maintains the same interface but uses the refactored components.
    """
    
    def __init__(self, project_id: str = None, 
                 location: str = None, 
                 processor_id: str = None):
        """
        Initialize the Document AI client.
        
        Args:
            project_id: Google Cloud project ID
            location: Location of the processor (e.g., 'us', 'eu')
            processor_id: ID of the Form Parser processor
        """
        logger.info("Initializing DocumentAIClient (using refactored components)")
        
        # Initialize the new components
        self.doc_ai_manager = DocumentAIManager(
            project_id=project_id,
            location=location,
            processor_id=processor_id
        )
        
        self.document_model = DocumentModel(self.doc_ai_manager)
        
        # For compatibility with legacy code
        self.processor_name = self.doc_ai_manager.processor_name
        self.client = self.doc_ai_manager.client
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document using Google Document AI Form Parser.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Processed document data including extracted checkboxes
        """
        logger.info(f"Processing document: {file_path}")
        
        # Use the new document model to process the file
        return self.document_model.process_file(file_path)
    
    def _extract_document_data(self, document) -> Dict[str, Any]:
        """
        Extract relevant data from the Document AI response.
        Kept for backward compatibility.
        
        Args:
            document: Document AI document object
            
        Returns:
            Dictionary containing extracted document data
        """
        # This is now handled by the DocumentModel
        return self.document_model._extract_document_data(document)
    
    def _extract_form_fields(self, page, text: str) -> List[Dict[str, Any]]:
        """
        Extract form fields from a page.
        Kept for backward compatibility.
        
        Args:
            page: Document AI page object
            text: Full document text
            
        Returns:
            List of dictionaries containing form field data
        """
        # This is now handled by the DocumentModel
        return self.document_model._extract_form_fields(page, text)
    
    def _extract_checkboxes(self, page, text: str) -> List[Dict[str, Any]]:
        """
        Extract checkbox information from a page.
        Kept for backward compatibility.
        
        Args:
            page: Document AI page object
            text: Full document text
            
        Returns:
            List of dictionaries containing checkbox data
        """
        # This is now handled by the DocumentModel
        return self.document_model._extract_checkboxes(page, text)
    
    def _get_text_from_layout(self, layout, text: str) -> str:
        """
        Extract text from a text layout element.
        Kept for backward compatibility.
        
        Args:
            layout: Text layout element
            text: Full document text
            
        Returns:
            Extracted text
        """
        # This is now handled by the DocumentModel
        return self.document_model._get_text_from_layout(layout, text) 