"""
Core Document AI functionality for the PDF Checkbox POC project.
Provides the DocumentAIManager class for handling Google Document AI operations.
"""

import logging
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions

# Import project configuration
from src.config import GCP_PROJECT_ID, GCP_LOCATION, GCP_PROCESSOR_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentAIManager:
    """Manager class for Google Document AI operations."""
    
    def __init__(self, 
                 project_id: Optional[str] = None, 
                 location: Optional[str] = None, 
                 processor_id: Optional[str] = None,
                 test_mode: bool = False):
        """Initialize the Document AI manager.
        
        Args:
            project_id: Google Cloud project ID
            location: Location of the processor (e.g., 'us', 'eu')
            processor_id: ID of the Form Parser processor
            test_mode: If True, skip actual Document AI connection (for testing)
            
        Raises:
            Exception: If connection to Document AI fails
        """
        self.project_id = project_id or GCP_PROJECT_ID
        self.location = location or GCP_LOCATION
        self.processor_id = processor_id or GCP_PROCESSOR_ID
        
        logger.debug(f"Initializing DocumentAIManager with:")
        logger.debug(f"project_id: {self.project_id}")
        logger.debug(f"location: {self.location}")
        logger.debug(f"processor_id: {self.processor_id}")
        logger.debug(f"test_mode: {test_mode}")
        
        if test_mode:
            # In test mode, we don't actually connect to Document AI
            logger.info("Initializing DocumentAIManager in test mode (no actual connection)")
            self.client = None
            self.processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
            return
            
        try:
            # Set client options for the API endpoint
            client_options = ClientOptions(
                api_endpoint=f"{self.location}-documentai.googleapis.com"
            )
            
            # Initialize Document AI client
            self.client = documentai.DocumentProcessorServiceClient(
                client_options=client_options
            )
            
            # Full resource name of the processor
            self.processor_name = self.client.processor_path(
                self.project_id, self.location, self.processor_id
            )
            
            logger.info(f"Successfully initialized Document AI manager")
            logger.info(f"Using processor: {self.processor_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Document AI manager: {e}")
            raise
    
    def process_document(self, file_content: bytes, mime_type: str = "application/pdf") -> documentai.Document:
        """
        Process a document using Google Document AI.
        
        Args:
            file_content: Binary content of the file to process
            mime_type: MIME type of the document
            
        Returns:
            Document AI processed document
            
        Raises:
            Exception: If document processing fails
        """
        if self.client is None:
            logger.warning("Cannot process document in test mode")
            return None
            
        try:
            # Configure the process request
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=documentai.RawDocument(
                    content=file_content,
                    mime_type=mime_type
                )
            )
            
            # Process the document
            logger.info(f"Processing document with Document AI")
            result = self.client.process_document(request=request)
            
            logger.info(f"Document processing successful")
            return result.document
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise 