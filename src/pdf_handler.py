"""
PDF document handler for uploading and processing PDF files.
"""

import os
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from werkzeug.utils import secure_filename

from src.config import UPLOAD_FOLDER, PROCESSED_FOLDER, ALLOWED_EXTENSIONS
from src.document_ai_client import DocumentAIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFHandler:
    """Handler for PDF document operations."""
    
    def __init__(self, document_ai_client: Optional[DocumentAIClient] = None):
        """
        Initialize the PDF handler.
        
        Args:
            document_ai_client: Document AI client instance
        """
        self.document_ai_client = document_ai_client or DocumentAIClient()
        
        # Ensure upload and processed directories exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(PROCESSED_FOLDER, exist_ok=True)
        
        logger.info(f"Initialized PDF handler with upload folder: {UPLOAD_FOLDER}")
    
    def allowed_file(self, filename: str) -> bool:
        """
        Check if the file has an allowed extension.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if the file extension is allowed, False otherwise
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def upload_pdf(self, file_storage) -> Dict[str, Any]:
        """
        Upload and save a PDF file.
        
        Args:
            file_storage: File storage object (e.g., from Flask request.files)
            
        Returns:
            Dictionary with file information
        """
        if not file_storage or not file_storage.filename:
            raise ValueError("No file provided")
        
        filename = secure_filename(file_storage.filename)
        if not self.allowed_file(filename):
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
        
        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Create a unique filename
        unique_filename = f"{file_id}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save the file
        file_storage.save(file_path)
        logger.info(f"Saved uploaded file: {file_path}")
        
        # Return file information
        return {
            "file_id": file_id,
            "original_filename": filename,
            "stored_filename": unique_filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path)
        }
    
    def process_pdf(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a PDF file using Document AI.
        
        Args:
            file_info: Dictionary with file information
            
        Returns:
            Dictionary with processing results
        """
        if not file_info or "file_path" not in file_info:
            raise ValueError("Invalid file information")
        
        file_path = file_info["file_path"]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Process the document with Document AI
        logger.info(f"Processing PDF: {file_path}")
        document_data = self.document_ai_client.process_document(file_path)
        
        # Add original filename to document data
        document_data["original_filename"] = file_info["original_filename"]
        
        # Save the processed data
        processed_filename = f"processed_{file_info['file_id']}.json"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
        
        with open(processed_path, 'w') as f:
            import json
            json.dump(document_data, f, indent=2)
        
        logger.info(f"Saved processed data: {processed_path}")
        
        # Return the processing results
        return {
            "file_id": file_info["file_id"],
            "original_filename": file_info["original_filename"],
            "processed_path": processed_path,
            "document_data": document_data
        }
    
    def extract_form_fields(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all form fields from processed document data.
        
        Args:
            document_data: Processed document data from Document AI
            
        Returns:
            List of dictionaries containing form field data
        """
        fields = []
        
        # Extract fields from the top-level fields array
        if "fields" in document_data:
            for field in document_data["fields"]:
                field_data = {
                    "page_number": field.get("page", 1),
                    "field_type": field.get("type", "text"),  # Default to text if not specified
                    "label": field.get("name", ""),
                    "value": field.get("value", ""),
                    "is_checked": field.get("value", False) if field.get("type") == "checkbox" else None,
                    "confidence": 1.0,  # Default confidence for detected fields
                    "bounding_box": field.get("bbox", []),
                    "normalized_bounding_box": field.get("bbox", [])  # Use same bbox for normalized
                }
                fields.append(field_data)
        
        # Also check each page for fields (for backward compatibility)
        for page in document_data.get("pages", []):
            page_number = page.get("page_number", 0)
            
            # Extract fields from the page
            for field in page.get("fields", []):
                # Skip if we already have this field (based on label and page)
                if any(f for f in fields 
                      if f["label"] == field.get("name", "") 
                      and f["page_number"] == field.get("page", 1)):
                    continue
                    
                field_data = {
                    "page_number": field.get("page", 1),
                    "field_type": field.get("type", "text"),  # Default to text if not specified
                    "label": field.get("name", ""),
                    "value": field.get("value", ""),
                    "is_checked": field.get("value", False) if field.get("type") == "checkbox" else None,
                    "confidence": 1.0,  # Default confidence for detected fields
                    "bounding_box": field.get("bbox", []),
                    "normalized_bounding_box": field.get("bbox", [])  # Use same bbox for normalized
                }
                fields.append(field_data)
        
        return fields
