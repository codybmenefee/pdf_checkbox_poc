"""
Google Document AI client for PDF checkbox extraction.
"""

from google.cloud import documentai_v1 as documentai
from google.auth import default
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Hardcoded configuration
GCP_CONFIG = {
    "project_id": "onespandemo",
    "location": "us",
    "processor_id": "f2a60f0653d61392"
}

class DocumentAIClient:
    """Client for interacting with Google Document AI Form Parser API."""
    
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
        try:
            # Get application default credentials
            credentials, detected_project = default()
            logger.debug(f"Successfully loaded application default credentials")
            logger.debug(f"Default project from credentials: {detected_project}")
            
            # Use hardcoded values first, then fall back to parameters
            self.project_id = GCP_CONFIG["project_id"]
            self.location = GCP_CONFIG["location"]
            self.processor_id = GCP_CONFIG["processor_id"]
            
            logger.debug(f"Using hardcoded configuration values:")
            logger.debug(f"project_id: {self.project_id}")
            logger.debug(f"location: {self.location}")
            logger.debug(f"processor_id: {self.processor_id}")
            
            # Initialize Document AI client with explicit endpoint
            client_options = {
                "api_endpoint": f"{self.location}-documentai.googleapis.com"
            }
            
            self.client = documentai.DocumentProcessorServiceClient(
                credentials=credentials,
                client_options=client_options
            )
            
            # Full resource name of the processor
            self.processor_name = self.client.processor_path(
                self.project_id, self.location, self.processor_id
            )
            
            logger.info(f"Successfully initialized Document AI client")
            logger.info(f"Using processor: {self.processor_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Document AI client: {str(e)}")
            raise
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document using Google Document AI Form Parser.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Processed document data including extracted checkboxes
        """
        # Read the file
        with open(file_path, "rb") as file:
            file_content = file.read()
        
        # Configure the process request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=documentai.RawDocument(
                content=file_content,
                mime_type="application/pdf"
            )
        )
        
        try:
            # Process the document
            logger.info(f"Processing document: {file_path}")
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract and return the processed data
            return self._extract_document_data(document)
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
    
    def _extract_document_data(self, document) -> Dict[str, Any]:
        """
        Extract relevant data from the Document AI response.
        
        Args:
            document: Document AI document object
            
        Returns:
            Dictionary containing extracted document data
        """
        try:
            # Extract document text
            text = document.text if hasattr(document, 'text') else ""
            logger.info(f"\n=== Document Summary ===")
            logger.info(f"Document mime_type: {document.mime_type if hasattr(document, 'mime_type') else 'unknown'}")
            logger.info(f"Document text length: {len(text)}")
            logger.info(f"Number of pages: {len(document.pages) if hasattr(document, 'pages') else 0}")
            
            # Extract document pages
            pages_data = []
            all_fields = []  # Track all fields across pages
            
            if hasattr(document, 'pages'):
                for page_idx, page in enumerate(document.pages):
                    logger.info(f"\n=== Processing Page {page_idx + 1} ===")
                    
                    # Get page dimensions if available
                    dimensions = {
                        "width": getattr(page.dimension, 'width', 0) if hasattr(page, 'dimension') else 0,
                        "height": getattr(page.dimension, 'height', 0) if hasattr(page, 'dimension') else 0,
                        "unit": getattr(page.dimension, 'unit', '') if hasattr(page, 'dimension') else ''
                    }
                    
                    # Extract form fields and checkboxes
                    form_fields = self._extract_form_fields(page, text)
                    checkboxes = self._extract_checkboxes(page, text)
                    
                    # Log form fields summary
                    if hasattr(page, 'form_fields'):
                        logger.info(f"Found {len(page.form_fields)} form fields")
                        for idx, field in enumerate(page.form_fields):
                            field_name = self._get_text_from_layout(field.field_name, text) if hasattr(field, 'field_name') else "NO_NAME"
                            field_value = self._get_text_from_layout(field.field_value, text) if hasattr(field, 'field_value') else "NO_VALUE"
                            field_type = getattr(field.field_value, 'value_type', 'NO_TYPE') if hasattr(field, 'field_value') else "NO_TYPE"
                            logger.info(f"Field {idx + 1}: Name='{field_name}' Value='{field_value}' Type='{field_type}'")
                    
                    # Create page data structure
                    page_data = {
                        "page_number": getattr(page, 'page_number', page_idx + 1),
                        "dimensions": dimensions,
                        "fields": []  # Will contain both form fields and checkboxes
                    }
                    
                    # Process form fields and checkboxes
                    for field in form_fields:
                        field_data = {
                            "id": f"field_{len(all_fields)}",
                            "type": field['type'],
                            "name": field['name'],
                            "value": field['value'],
                            "bbox": field['bbox'],
                            "page": page_data["page_number"]
                        }
                        page_data["fields"].append(field_data)
                        all_fields.append(field_data)
                        logger.info(f"Added {'checkbox' if field['is_checkbox'] else 'text'} field: {field['name']}")
                    
                    # Add any additional checkboxes from symbol detection
                    for checkbox in checkboxes:
                        if checkbox.get('label'):  # Only add if we have a label
                            field_data = {
                                "id": f"checkbox_{len(all_fields)}",
                                "type": "checkbox",
                                "name": checkbox['label'],
                                "value": checkbox['is_checked'],
                                "bbox": checkbox['normalized_bounding_box'],
                                "page": page_data["page_number"]
                            }
                            page_data["fields"].append(field_data)
                            all_fields.append(field_data)
                            logger.info(f"Added symbol checkbox: {checkbox['label']}")
                    
                    pages_data.append(page_data)
                    
                    # Log extraction results
                    logger.info(f"Extracted {len(checkboxes)} symbol checkboxes")
                    logger.info(f"Extracted {len(form_fields)} form fields")
                    logger.info(f"Total fields on page: {len(page_data['fields'])}")
                
                # Construct the final document data
                document_data = {
                    "text": text,
                    "pages": pages_data,
                    "mime_type": getattr(document, 'mime_type', 'application/pdf'),
                    "fields": all_fields  # Include all fields at the top level
                }
                
                # Log final summary
                logger.info(f"\n=== Document Processing Summary ===")
                logger.info(f"Total fields detected: {len(all_fields)}")
                logger.info(f"Total pages processed: {len(pages_data)}")
                
                return document_data
                
        except Exception as e:
            logger.error(f"Error extracting document data: {str(e)}")
            raise
    
    def _extract_checkboxes(self, page, text: str) -> List[Dict[str, Any]]:
        """
        Extract checkbox information from a page.
        
        Args:
            page: Document AI page object
            text: Full document text
            
        Returns:
            List of dictionaries containing checkbox data
        """
        checkboxes = []
        
        try:
            # Process detected symbols (which include checkboxes)
            if hasattr(page, 'detected_symbols') and page.detected_symbols:
                logger.debug(f"\n=== Processing Detected Symbols ===")
                for symbol in page.detected_symbols:
                    try:
                        # Log symbol attributes for debugging
                        logger.debug("\nProcessing symbol:")
                        for attr in dir(symbol):
                            if not attr.startswith('_'):
                                try:
                                    value = getattr(symbol, attr)
                                    if not callable(value):
                                        logger.debug(f"  {attr}: {value}")
                                except Exception as e:
                                    logger.debug(f"  {attr}: Error accessing - {str(e)}")
                        
                        # Get symbol type and state
                        symbol_type = getattr(symbol, 'symbol_type', None)
                        symbol_state = getattr(symbol, 'state', None)
                        
                        # Check if this is a checkbox using string comparison since we can't rely on enum
                        if str(symbol_type).endswith('CHECKBOX'):
                            # Get the layout and text anchor if available
                            layout = getattr(symbol, 'layout', None)
                            text_anchor = getattr(layout, 'text_anchor', None) if layout else None
                            
                            # Try to get associated text (label) near the checkbox
                            label = None
                            if text_anchor:
                                label = self._get_text_from_layout({'text_anchor': text_anchor}, text)
                            
                            checkbox_data = {
                                "is_checked": str(symbol_state).endswith('CHECKED'),
                                "confidence": getattr(symbol, 'confidence', 0.0),
                                "label": label,
                                "bounding_box": self._extract_bounding_box(
                                    getattr(layout, 'bounding_poly', None) if layout else None
                                ),
                                "normalized_bounding_box": self._extract_normalized_bounding_box(
                                    getattr(layout, 'bounding_poly', None) if layout else None
                                )
                            }
                            logger.debug(f"Extracted checkbox data: {json.dumps(checkbox_data, indent=2)}")
                            checkboxes.append(checkbox_data)
                    
                    except Exception as symbol_error:
                        logger.error(f"Error processing symbol: {str(symbol_error)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error extracting checkboxes: {str(e)}")
            # Continue processing even if checkbox extraction fails
            pass
        
        return checkboxes
    
    def _extract_form_fields(self, page, text: str) -> List[Dict[str, Any]]:
        """Extract form fields from a page."""
        form_fields = []
        try:
            if not hasattr(page, 'form_fields'):
                return form_fields

            # Known W-9 checkbox field names
            w9_checkbox_fields = [
                'individual/sole proprietor',
                'c corporation',
                's corporation',
                'partnership',
                'trust/estate',
                'limited liability company',
                'other',
                'llc'
            ]

            for field in page.form_fields:
                try:
                    field_name = self._get_text_from_layout(field.field_name, text) if hasattr(field, 'field_name') else ""
                    field_value = self._get_text_from_layout(field.field_value, text) if hasattr(field, 'field_value') else ""
                    
                    # Get field value type if available
                    value_type = ""
                    if hasattr(field, 'field_value') and hasattr(field.field_value, 'value_type'):
                        value_type = str(field.field_value.value_type)
                    
                    # Check if this is a checkbox field
                    is_checkbox = False
                    is_checked = False
                    field_type = "text"  # Default to text field
                    
                    # Method 1: Check value type
                    if value_type and ('CHECKBOX' in value_type.upper() or 'SELECTED' in value_type.upper()):
                        is_checkbox = True
                        field_type = "checkbox"
                        is_checked = field_value.lower() in ['true', 'yes', 'checked', '✓', '✔', 'x']
                    
                    # Method 2: Check field name against known W-9 checkboxes
                    field_name_lower = field_name.lower().strip()
                    if any(checkbox_field in field_name_lower for checkbox_field in w9_checkbox_fields):
                        is_checkbox = True
                        field_type = "checkbox"
                        # For W-9 forms, an empty value typically means unchecked
                        is_checked = bool(field_value.strip())
                    
                    # Method 3: Check field name for checkbox indicators
                    checkbox_terms = ['check', 'checkbox', 'tick', 'mark', 'select', 'choice', 'option']
                    if any(term in field_name_lower for term in checkbox_terms):
                        is_checkbox = True
                        field_type = "checkbox"
                        is_checked = field_value.lower() in ['true', 'yes', 'checked', '✓', '✔', 'x']
                    
                    # Method 4: Check field value for checkbox characters
                    checkbox_chars = ['✓', '✔', '☑', '☒', '■', '□', '▢', '▣', 'x', 'X', '[ ]', '[x]', '[X]']
                    if any(char in field_value for char in checkbox_chars):
                        is_checkbox = True
                        field_type = "checkbox"
                        is_checked = any(char in field_value for char in ['✓', '✔', '☑', '▣', 'x', 'X', '[x]', '[X]'])
                    
                    # Method 5: Check if field is empty (common for unchecked checkboxes)
                    if not is_checkbox and not field_value.strip() and field_name_lower:
                        # Look for patterns common in form labels
                        if any(pattern in field_name_lower for pattern in ['corporation', 'individual', 'partnership', 'trust', 'estate', 'llc']):
                            is_checkbox = True
                            field_type = "checkbox"
                            is_checked = False
                    
                    # Get bounding box if available
                    bbox = None
                    if hasattr(field.field_name, 'bounding_poly'):
                        vertices = field.field_name.bounding_poly.normalized_vertices
                        if vertices:
                            bbox = {
                                'left': vertices[0].x,
                                'top': vertices[0].y,
                                'right': vertices[2].x,
                                'bottom': vertices[2].y
                            }
                    
                    form_field = {
                        'name': field_name,
                        'value': field_value if not is_checkbox else is_checked,
                        'type': field_type,
                        'value_type': value_type,
                        'is_checkbox': is_checkbox,
                        'is_checked': is_checked if is_checkbox else None,
                        'bbox': bbox,
                        'page_number': getattr(page, 'page_number', 1)
                    }
                    
                    # Log field detection
                    if is_checkbox:
                        logger.info(f"Detected checkbox: {field_name} (checked: {is_checked})")
                    else:
                        logger.info(f"Detected text field: {field_name} (value: {field_value})")
                    
                    form_fields.append(form_field)
                    
                except Exception as e:
                    logger.error(f"Error processing form field: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Error extracting form fields: {str(e)}")
        
        return form_fields
    
    def _get_text_from_layout(self, layout, text: str) -> str:
        """
        Extract text from a layout object using text anchors.
        
        Args:
            layout: Document AI layout object
            text: Full document text
            
        Returns:
            Extracted text string
        """
        try:
            if not layout:
                return ""
            
            # Get the text anchor from the layout object
            text_anchor = None
            
            # Try different ways to access text_anchor based on the object structure
            if hasattr(layout, 'text_anchor'):
                text_anchor = layout.text_anchor
            elif hasattr(layout, 'layout') and hasattr(layout.layout, 'text_anchor'):
                text_anchor = layout.layout.text_anchor
            elif hasattr(layout, 'layout') and layout.layout:
                # Handle nested layout objects
                for field in ['text_anchor', 'text_segments', 'text']:
                    if hasattr(layout.layout, field):
                        if field == 'text_anchor':
                            text_anchor = getattr(layout.layout, field)
                            break
                        elif field == 'text_segments':
                            segments = getattr(layout.layout, field)
                            if segments:
                                return "".join(seg.text for seg in segments if hasattr(seg, 'text'))
                        elif field == 'text':
                            return getattr(layout.layout, field)
            
            if not text_anchor or not hasattr(text_anchor, 'text_segments'):
                return ""
            
            # Extract text from segments
            result = ""
            for segment in text_anchor.text_segments:
                start_index = int(segment.start_index) if hasattr(segment, 'start_index') else 0
                end_index = int(segment.end_index) if hasattr(segment, 'end_index') else 0
                if 0 <= start_index < len(text) and 0 <= end_index <= len(text):
                    result += text[start_index:end_index]
            
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from layout: {str(e)}")
            return ""
    
    def _extract_bounding_box(self, bounding_poly) -> List[Dict[str, float]]:
        """
        Extract bounding box coordinates.
        
        Args:
            bounding_poly: Document AI bounding polygon
            
        Returns:
            List of vertex coordinates
        """
        if not bounding_poly or not bounding_poly.vertices:
            return []
        
        vertices = []
        for vertex in bounding_poly.vertices:
            vertices.append({
                "x": vertex.x if hasattr(vertex, 'x') else 0,
                "y": vertex.y if hasattr(vertex, 'y') else 0
            })
        
        return vertices
    
    def _extract_normalized_bounding_box(self, bounding_poly) -> List[Dict[str, float]]:
        """
        Extract normalized bounding box coordinates.
        
        Args:
            bounding_poly: Document AI bounding polygon
            
        Returns:
            List of normalized vertex coordinates
        """
        if not bounding_poly or not bounding_poly.normalized_vertices:
            return []
        
        vertices = []
        for vertex in bounding_poly.normalized_vertices:
            vertices.append({
                "x": vertex.x if hasattr(vertex, 'x') else 0,
                "y": vertex.y if hasattr(vertex, 'y') else 0
            })
        
        return vertices
