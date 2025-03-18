"""
Visualization tools for document processing results.
"""

import os
from typing import List, Dict, Any, Optional
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def visualize_template(pdf_path: str, template_data: Dict[str, Any], output_dir: str) -> List[str]:
    """
    Create visualizations of the template fields overlaid on the PDF pages.
    
    Args:
        pdf_path: Path to the original PDF file
        template_data: Template data containing fields and their locations
        output_dir: Directory to save the visualizations
        
    Returns:
        List of paths to the generated visualization images
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path)
        output_paths = []
        
        # Process each page
        for page_idx, page_image in enumerate(pages):
            # Create a copy of the page image for drawing
            draw_image = page_image.copy()
            draw = ImageDraw.Draw(draw_image)
            
            # Get page dimensions
            page_width, page_height = page_image.size
            
            # Find fields for this page
            page_fields = [f for f in template_data.get("fields", []) if f.get("page") == page_idx + 1]
            
            # Draw each field
            for field in page_fields:
                bbox = field.get("bbox", {})
                if not bbox:
                    continue
                
                # Convert normalized coordinates to pixel coordinates
                left = bbox.get("left", 0) * page_width
                top = bbox.get("top", 0) * page_height
                right = bbox.get("right", 0) * page_width
                bottom = bbox.get("bottom", 0) * page_height
                
                # Choose color based on field type
                color = "red" if field.get("type") == "checkbox" else "blue"
                
                # Draw bounding box
                draw.rectangle([left, top, right, bottom], outline=color, width=2)
                
                # Draw field name
                draw.text((left, top - 10), field.get("name", ""), fill=color)
                
                # For checkboxes, indicate state
                if field.get("type") == "checkbox":
                    state = "✓" if field.get("value") else "☐"
                    draw.text((left + 2, top + 2), state, fill=color)
            
            # Save the visualization
            output_path = os.path.join(output_dir, f"visualization_page_{page_idx + 1}.png")
            draw_image.save(output_path)
            output_paths.append(output_path)
            
            logger.info(f"Generated visualization for page {page_idx + 1}: {output_path}")
        
        return output_paths
        
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        raise

def visualize_checkboxes_with_confidence(
    pdf_path: str,
    checkboxes: List[Dict[str, Any]],
    output_dir: str,
    high_confidence_threshold: float = 0.9,
    medium_confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Create advanced visualizations of checkbox detection results with confidence scoring.
    
    Args:
        pdf_path: Path to the original PDF file
        checkboxes: List of detected checkboxes with confidence scores
        output_dir: Directory to save the visualizations
        high_confidence_threshold: Threshold for high confidence (default: 0.9)
        medium_confidence_threshold: Threshold for medium confidence (default: 0.7)
        
    Returns:
        Dict containing visualization data including page images and checkbox metadata
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path)
        
        # Prepare visualization data
        visualization_data = {
            "document_name": os.path.basename(pdf_path),
            "processing_date": datetime.now().isoformat(),
            "total_pages": len(pages),
            "pages": [],
            "checkboxes": []
        }
        
        # Add IDs to checkboxes if they don't have one
        for i, checkbox in enumerate(checkboxes):
            if "id" not in checkbox:
                checkbox["id"] = str(uuid.uuid4())
            
            # Add confidence category
            confidence = checkbox.get("confidence", 0.0)
            if confidence >= high_confidence_threshold:
                checkbox["confidence_category"] = "high"
            elif confidence >= medium_confidence_threshold:
                checkbox["confidence_category"] = "medium"
            else:
                checkbox["confidence_category"] = "low"
        
        # Process each page
        for page_idx, page_image in enumerate(pages):
            page_number = page_idx + 1
            
            # Create a copy of the page image for drawing
            draw_image = page_image.copy()
            draw = ImageDraw.Draw(draw_image)
            
            # Get page dimensions
            page_width, page_height = page_image.size
            
            # Find checkboxes for this page
            page_checkboxes = [cb for cb in checkboxes if cb.get("page") == page_number]
            
            # Draw each checkbox with color based on confidence
            for checkbox in page_checkboxes:
                bbox = checkbox.get("bbox", {})
                if not bbox:
                    continue
                
                # Convert normalized coordinates to pixel coordinates
                left = bbox.get("left", 0) * page_width
                top = bbox.get("top", 0) * page_height
                right = bbox.get("right", 0) * page_width
                bottom = bbox.get("bottom", 0) * page_height
                
                # Get confidence score and determine color
                confidence = checkbox.get("confidence", 0.0)
                confidence_category = checkbox.get("confidence_category", "low")
                
                if confidence_category == "high":
                    color = "green"
                elif confidence_category == "medium":
                    color = "orange"
                else:
                    color = "red"
                
                # Draw bounding box
                draw.rectangle([left, top, right, bottom], outline=color, width=3)
                
                # Draw confidence score
                confidence_text = f"{confidence:.2f}"
                draw.text((left, top - 15), confidence_text, fill=color)
                
                # Draw checkbox label if available
                label = checkbox.get("label", "")
                if label:
                    draw.text((left, bottom + 5), label, fill=color)
                
                # For checkboxes, indicate state
                state = "✓" if checkbox.get("value") else "☐"
                draw.text((left + 2, top + 2), state, fill=color)
            
            # Save the visualization
            output_path = os.path.join(output_dir, f"checkbox_vis_page_{page_number}.png")
            draw_image.save(output_path)
            
            # Add page data to visualization data
            visualization_data["pages"].append({
                "page_number": page_number,
                "image_url": f"/static/visualizations/checkbox_vis_page_{page_number}.png",
                "width": page_width,
                "height": page_height
            })
            
            logger.info(f"Generated checkbox visualization for page {page_number}: {output_path}")
        
        # Add checkboxes to visualization data
        visualization_data["checkboxes"] = checkboxes
        
        # Save visualization metadata
        metadata_path = os.path.join(output_dir, "checkbox_visualization_data.json")
        with open(metadata_path, "w") as f:
            json.dump(visualization_data, f, indent=2)
        
        return visualization_data
        
    except Exception as e:
        logger.error(f"Error creating checkbox visualization: {str(e)}")
        raise

def get_checkbox_visualization_data(visualization_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve visualization data for a given visualization ID.
    
    Args:
        visualization_id: ID of the visualization
        
    Returns:
        Dict containing visualization data or None if not found
    """
    try:
        # In a real implementation, this would retrieve data from a database
        # For now, we'll load from a JSON file in the visualizations directory
        from src.config import PROCESSED_FOLDER
        
        vis_dir = os.path.join(PROCESSED_FOLDER, "visualizations", visualization_id)
        metadata_path = os.path.join(vis_dir, "checkbox_visualization_data.json")
        
        if not os.path.exists(metadata_path):
            logger.error(f"Visualization metadata not found: {metadata_path}")
            return None
        
        with open(metadata_path, "r") as f:
            visualization_data = json.load(f)
        
        return visualization_data
        
    except Exception as e:
        logger.error(f"Error retrieving visualization data: {str(e)}")
        return None

def export_checkbox_data(export_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export checkbox data to a standardized JSON format.
    
    Args:
        export_data: Data to be exported
        
    Returns:
        Dict containing processed export data
    """
    try:
        # Process the export data if needed
        processed_data = {
            "document_id": export_data.get("document_id"),
            "document_name": export_data.get("document_name"),
            "export_date": export_data.get("export_date", datetime.now().isoformat()),
            "checkboxes": export_data.get("checkboxes", [])
        }
        
        # In a real implementation, you might store this in a database or file system
        # For now, we'll just return the processed data
        return processed_data
        
    except Exception as e:
        logger.error(f"Error exporting checkbox data: {str(e)}")
        raise

def save_checkbox_corrections(corrections_data: Dict[str, Any]) -> bool:
    """
    Save manually corrected checkbox data.
    
    Args:
        corrections_data: Data containing the corrections
        
    Returns:
        Boolean indicating success
    """
    try:
        document_id = corrections_data.get("document_id")
        corrections = corrections_data.get("corrections", [])
        
        if not document_id or not corrections:
            logger.error("Missing document ID or corrections in the correction data")
            return False
        
        # In a real implementation, this would update the database
        # For now, we'll just log the corrections
        logger.info(f"Saving {len(corrections)} corrections for document {document_id}")
        
        # Return success
        return True
        
    except Exception as e:
        logger.error(f"Error saving checkbox corrections: {str(e)}")
        return False

def visualize_extracted_fields(
    pdf_path: str,
    fields_data: List[Dict[str, Any]],
    output_dir: str
) -> Dict[str, Any]:
    """
    Create visualizations of extracted fields overlaid on the PDF pages.
    
    Args:
        pdf_path: Path to the original PDF file
        fields_data: List of extracted fields with their locations and values
        output_dir: Directory to save the visualizations
        
    Returns:
        Dictionary containing visualization data including image paths and fields data
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path)
        
        result = {
            "document_id": os.path.basename(output_dir),
            "document_name": os.path.basename(pdf_path),
            "processing_date": datetime.now().isoformat(),
            "pages": [],
            "fields": []
        }
        
        # Process and normalize field data
        processed_fields = []
        for field in fields_data:
            # Ensure field has an ID
            if "id" not in field:
                field["id"] = str(uuid.uuid4())
                
            # Make a copy to avoid modifying the original
            processed_field = field.copy()
            processed_fields.append(processed_field)
            
        # Save page images and prepare visualization data
        for page_idx, page_image in enumerate(pages):
            # Save the page image
            page_number = page_idx + 1
            image_path = os.path.join(output_dir, f"page_{page_number}.png")
            page_image.save(image_path)
            
            # Add page data to result
            result["pages"].append({
                "page_number": page_number,
                "image_url": f"/api/visualizations/{result['document_id']}/page_{page_number}.png",
                "width": page_image.width,
                "height": page_image.height
            })
            
            # Update page number for fields on this page
            for field in processed_fields:
                if field.get("page") == page_number:
                    # Ensure the field has a bbox dictionary
                    if "bbox" not in field or not field["bbox"]:
                        field["bbox"] = {
                            "left": 0,
                            "top": 0,
                            "width": 0,
                            "height": 0
                        }
                        logger.warning(f"Field {field.get('id', 'unknown')} missing bbox, using defaults")
                        continue
                    
                    bbox = field["bbox"]
                    normalized_bbox = {}
                    
                    # Normalize coordinates to [0,1] range depending on format
                    if all(key in bbox for key in ["left", "top", "right", "bottom"]):
                        # If using left/top/right/bottom format
                        if any(bbox[key] > 1 for key in ["left", "top", "right", "bottom"]):
                            # Convert absolute coordinates to normalized
                            normalized_bbox = {
                                "left": bbox["left"] / page_image.width,
                                "top": bbox["top"] / page_image.height,
                                "right": bbox["right"] / page_image.width,
                                "bottom": bbox["bottom"] / page_image.height
                            }
                        else:
                            # Already normalized
                            normalized_bbox = bbox.copy()
                            
                        # Also add width/height format for consistency
                        normalized_bbox["width"] = normalized_bbox["right"] - normalized_bbox["left"]
                        normalized_bbox["height"] = normalized_bbox["bottom"] - normalized_bbox["top"]
                        
                    elif all(key in bbox for key in ["left", "top", "width", "height"]):
                        # If using left/top/width/height format
                        if any(bbox[key] > 1 for key in ["left", "top", "width", "height"]):
                            # Convert absolute coordinates to normalized
                            normalized_bbox = {
                                "left": bbox["left"] / page_image.width,
                                "top": bbox["top"] / page_image.height,
                                "width": bbox["width"] / page_image.width,
                                "height": bbox["height"] / page_image.height
                            }
                        else:
                            # Already normalized
                            normalized_bbox = bbox.copy()
                            
                        # Also add right/bottom format for consistency
                        normalized_bbox["right"] = normalized_bbox["left"] + normalized_bbox["width"]
                        normalized_bbox["bottom"] = normalized_bbox["top"] + normalized_bbox["height"]
                        
                    else:
                        logger.warning(f"Field {field.get('id', 'unknown')} has invalid bbox format")
                        continue
                    
                    # Update field with normalized bbox
                    field["bbox"] = normalized_bbox
        
        # Add processed fields to result
        result["fields"] = processed_fields
        
        # Save visualization metadata
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(result, f, indent=2)
            
        return result
        
    except Exception as e:
        logger.error(f"Error creating field visualizations: {e}")
        raise

def get_field_visualization_data(visualization_id: str) -> Optional[Dict[str, Any]]:
    """
    Get field visualization data for a specific document.
    
    Args:
        visualization_id: ID of the visualization
        
    Returns:
        Visualization data or None if not found
    """
    try:
        visualization_dir = os.path.join("static", "visualizations", visualization_id)
        metadata_path = os.path.join(visualization_dir, "metadata.json")
        
        if not os.path.exists(metadata_path):
            return None
            
        with open(metadata_path, "r") as f:
            data = json.load(f)
            
        return data
        
    except Exception as e:
        logger.error(f"Error getting field visualization data: {e}")
        return None

def export_field_data(export_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export field data in a format suitable for external systems.
    
    Args:
        export_data: Export request data containing document ID
        
    Returns:
        Dictionary containing the exported field data
    """
    try:
        document_id = export_data.get("document_id")
        if not document_id:
            raise ValueError("Document ID is required")
            
        visualization_data = get_field_visualization_data(document_id)
        if not visualization_data:
            raise ValueError(f"No visualization data found for document ID: {document_id}")
            
        # Create export data structure
        result = {
            "document_id": document_id,
            "document_name": visualization_data.get("document_name", ""),
            "export_date": datetime.now().isoformat(),
            "fields": visualization_data.get("fields", [])
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error exporting field data: {e}")
        raise

def save_field_corrections(corrections_data: Dict[str, Any]) -> bool:
    """
    Save field correction data.
    
    Args:
        corrections_data: Dict containing field correction data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if "visualization_id" not in corrections_data or "fields" not in corrections_data:
            logger.error("Missing required data in corrections")
            return False
        
        visualization_id = corrections_data["visualization_id"]
        fields = corrections_data["fields"]
        
        # Load existing data file
        visualization_dir = os.path.join("static", "visualizations", visualization_id)
        data_file = os.path.join(visualization_dir, "field_data.json")
        
        if not os.path.exists(data_file):
            logger.error(f"Visualization data file not found: {data_file}")
            return False
        
        with open(data_file, 'r') as f:
            visualization_data = json.load(f)
        
        # Update fields
        visualization_data["fields"] = fields
        
        # Save updated data
        with open(data_file, 'w') as f:
            json.dump(visualization_data, f, indent=2)
        
        logger.info(f"Saved field corrections for visualization {visualization_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving field corrections: {str(e)}")
        return False

def generate_test_document_pages(pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Generate page images for a test document.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the page images
        
    Returns:
        List of page data with image URLs
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path)
        page_data = []
        
        # Process each page
        for page_idx, page_image in enumerate(pages):
            page_number = page_idx + 1
            
            # Save the page image
            image_filename = f"page_{page_number}.png"
            image_path = os.path.join(output_dir, image_filename)
            page_image.save(image_path)
            
            # Get page dimensions
            width, height = page_image.size
            
            # Add page data
            page_data.append({
                "page_number": page_number,
                "image_url": f"/api/visualizations/{os.path.basename(output_dir)}/{image_filename}",
                "width": width,
                "height": height
            })
            
            logger.info(f"Generated page image for page {page_number}: {image_path}")
        
        return page_data
        
    except Exception as e:
        logger.error(f"Error generating test document pages: {str(e)}")
        raise 