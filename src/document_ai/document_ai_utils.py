"""
Utility functions for Document AI operations.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
import os
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_document_structure(document: Any) -> Tuple[bool, str, float]:
    """
    Validates that a document has the necessary structure for processing.
    
    Args:
        document: Document AI document object
        
    Returns:
        Tuple of (is_valid, error_message, confidence_score)
    """
    confidence = 1.0
    
    # Check if document is None
    if document is None:
        return False, "Document is None", 0.0
    
    # Check for pages
    if not hasattr(document, 'pages') or not document.pages:
        return False, "Document has no pages", 0.0
    
    # Check document text
    if not hasattr(document, 'text') or not document.text:
        confidence *= 0.7
        logger.warning("Document has no text content")
    
    # Check page quality and orientation
    for i, page in enumerate(document.pages):
        # Check if page has dimensions
        if not hasattr(page, 'dimension'):
            confidence *= 0.9
            logger.warning(f"Page {i+1} has no dimension information")
            
        # Check for rotated pages
        if hasattr(page, 'rotation') and getattr(page, 'rotation', 0) != 0:
            confidence *= 0.8
            logger.warning(f"Page {i+1} is rotated")
    
    if confidence < 0.6:
        return False, "Document structure is too poor for reliable processing", confidence
        
    return True, "Document structure is valid", confidence

def normalize_bounding_box(bbox: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Normalize a bounding box to a standard format.
    
    Args:
        bbox: List of points that form the bounding box
        
    Returns:
        Dictionary with normalized coordinates
    """
    if not bbox or len(bbox) < 4:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    
    # Find min/max x and y
    min_x = min(point["x"] for point in bbox)
    min_y = min(point["y"] for point in bbox)
    max_x = max(point["x"] for point in bbox)
    max_y = max(point["y"] for point in bbox)
    
    # Calculate width and height
    width = max_x - min_x
    height = max_y - min_y
    
    return {
        "x": min_x,
        "y": min_y,
        "width": width,
        "height": height
    }

def save_document_as_json(document_data: Dict[str, Any], output_path: str, fixed_timestamp: Optional[str] = None) -> str:
    """
    Save extracted document data as JSON.
    
    Args:
        document_data: Document data to save
        output_path: Directory to save the JSON file
        fixed_timestamp: Optional fixed timestamp for testing purposes
        
    Returns:
        Path to the saved JSON file
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Generate filename
        timestamp = fixed_timestamp if fixed_timestamp else datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"document_{timestamp}.json"
        file_path = os.path.join(output_path, filename)
        
        # Save JSON file
        with open(file_path, "w") as f:
            json.dump(document_data, f, indent=2)
        
        logger.info(f"Saved document data to {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving document data: {e}")
        raise

def get_confidence_score(entity) -> float:
    """
    Extract confidence score from a Document AI entity.
    
    Args:
        entity: Document AI entity
        
    Returns:
        Confidence score between 0 and 1
    """
    if hasattr(entity, 'confidence'):
        return entity.confidence
    return 0.0

def encode_image_for_visualization(image_path: str) -> str:
    """
    Encode an image as base64 for web visualization.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64-encoded image data URI
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            mime_type = "image/jpeg"  # Default mime type
            
            # Determine mime type from extension
            if image_path.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_path.lower().endswith('.gif'):
                mime_type = "image/gif"
            elif image_path.lower().endswith('.pdf'):
                mime_type = "application/pdf"
            
            return f"data:{mime_type};base64,{encoded_string}"
            
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return ""

def generate_color_for_field(field_type: str) -> str:
    """
    Generate a consistent color based on field type for visualization.
    
    Args:
        field_type: Type of the field
        
    Returns:
        Hex color code
    """
    color_map = {
        "checkbox": "#FF5733",  # Orange-red
        "text": "#33A8FF",      # Blue
        "number": "#33FF57",    # Green
        "date": "#FF33F5"       # Pink
    }
    
    return color_map.get(field_type.lower(), "#AAAAAA")  # Default gray

def generate_visualization_data(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate data structure for document visualization.
    
    Args:
        document_data: Extracted document data
        
    Returns:
        Data structure for visualization
    """
    visualization_data = {
        "pages": [],
        "fields": []
    }
    
    # Process each page
    for page in document_data.get("pages", []):
        page_data = {
            "page_number": page.get("page_number", 0),
            "width": page.get("dimensions", {}).get("width", 0),
            "height": page.get("dimensions", {}).get("height", 0),
            "elements": []
        }
        
        # Add elements from the page's fields
        for field in page.get("fields", []):
            element = {
                "id": field.get("id", ""),
                "type": field.get("type", ""),
                "name": field.get("name", ""),
                "value": field.get("value", ""),
                "bbox": field.get("bbox", []),
                "color": generate_color_for_field(field.get("type", ""))
            }
            page_data["elements"].append(element)
            
            # Also add to the overall fields list
            visualization_data["fields"].append({
                "id": field.get("id", ""),
                "page": page.get("page_number", 0),
                "name": field.get("name", ""),
                "type": field.get("type", ""),
                "value": field.get("value", "")
            })
        
        visualization_data["pages"].append(page_data)
    
    return visualization_data 