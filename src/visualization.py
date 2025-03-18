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

def test_pdf_rendering(pdf_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Test if a PDF can be properly rendered to images.
    
    Args:
        pdf_path: Path to the PDF file to test
        output_dir: Directory to save the test images
        
    Returns:
        Dictionary with test results
    """
    result = {
        "success": False,
        "pdf_path": pdf_path,
        "pdf_exists": os.path.exists(pdf_path),
        "pdf_size": 0,
        "output_dir": output_dir,
        "pages": [],
        "error": None
    }
    
    try:
        # Check if PDF exists
        if not os.path.exists(pdf_path):
            result["error"] = f"PDF file not found: {pdf_path}"
            return result
            
        # Check file size
        file_size = os.path.getsize(pdf_path)
        result["pdf_size"] = file_size
        
        if file_size == 0:
            result["error"] = f"PDF file is empty: {pdf_path}"
            return result
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Try different page rendering libraries
        # First try pdf2image
        try:
            logger.info(f"Converting PDF to images using pdf2image: {pdf_path}")
            pages = convert_from_path(pdf_path, dpi=150)
            logger.info(f"Successfully converted {len(pages)} pages")
            
            # Save page images
            for i, page in enumerate(pages):
                page_num = i + 1
                image_path = os.path.join(output_dir, f"test_page_{page_num}.png")
                page.save(image_path)
                
                result["pages"].append({
                    "page_number": page_num,
                    "width": page.width,
                    "height": page.height,
                    "image_path": image_path,
                    "image_size": os.path.getsize(image_path)
                })
                
            result["success"] = True
                
        except Exception as e:
            logger.error(f"Error converting PDF with pdf2image: {str(e)}")
            result["pdf2image_error"] = str(e)
            
            # Try using PyPDF2 as a fallback
            try:
                import PyPDF2
                
                with open(pdf_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    num_pages = len(pdf.pages)
                    
                    result["pages"] = [{
                        "page_number": i+1,
                        "width": 0,
                        "height": 0,
                        "image_path": None
                    } for i in range(num_pages)]
                    
                    result["success"] = True
                    result["pypdf2_only"] = True
                    
            except Exception as pdf_error:
                logger.error(f"Error reading PDF with PyPDF2: {str(pdf_error)}")
                result["pypdf2_error"] = str(pdf_error)
                result["error"] = f"Failed to read PDF with any method: {str(e)}, {str(pdf_error)}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in test_pdf_rendering: {str(e)}")
        result["error"] = str(e)
        return result

def visualize_extracted_fields(
    pdf_path: str,
    fields_data: List[Dict[str, Any]],
    output_dir: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Create visualizations of extracted fields overlaid on the PDF pages.
    
    Args:
        pdf_path: Path to the original PDF file
        fields_data: List of extracted fields with their locations and values
        output_dir: Directory to save the visualizations
        force: Force regeneration even if files exist
        
    Returns:
        Dictionary containing visualization data including image paths and fields data
    """
    try:
        logger.info(f"Visualizing extracted fields from {pdf_path} to {output_dir}")
        logger.info(f"Number of fields to visualize: {len(fields_data)}")
        logger.info(f"Force regeneration: {force}")
        
        # Check if visualization already exists and we're not forcing regeneration
        if not force and os.path.exists(output_dir):
            page_files = [f for f in os.listdir(output_dir) if f.startswith("page_") and (f.endswith(".png") or f.endswith(".jpg"))]
            if page_files:
                logger.info(f"Using existing {len(page_files)} visualization files in {output_dir}")
                
                # Return existing visualization data
                existing_data = {
                    "document_id": os.path.basename(output_dir),
                    "document_name": os.path.basename(pdf_path),
                    "processing_date": datetime.now().isoformat(),
                    "total_pages": len(page_files),
                    "pages": [],
                    "fields": fields_data
                }
                
                for filename in sorted(page_files):
                    if filename.startswith("page_") and (filename.endswith(".png") or filename.endswith(".jpg")):
                        extension = filename.split(".")[-1]
                        page_num = int(filename.replace(f"page_", "").replace(f".{extension}", ""))
                        
                        # Get image dimensions
                        try:
                            img = Image.open(os.path.join(output_dir, filename))
                            width, height = img.size
                            img.close()
                        except Exception as img_error:
                            logger.warning(f"Could not open image to get dimensions: {str(img_error)}")
                            width, height = 0, 0
                        
                        existing_data["pages"].append({
                            "page_number": page_num,
                            "image_url": f"/static/visualizations/{existing_data['document_id']}/{filename}",
                            "alternate_url": f"/api/visualizations/{existing_data['document_id']}/{filename}",
                            "width": width,
                            "height": height
                        })
                
                # Add field distribution by page (for UI)
                existing_data["fields_by_page"] = {}
                for field in fields_data:
                    page = field.get("page", 1)
                    if page not in existing_data["fields_by_page"]:
                        existing_data["fields_by_page"][page] = []
                    existing_data["fields_by_page"][page].append(field["field_id"])
                
                return existing_data
        
        # Check if PDF path exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            # First try to test if this is a PDF reading issue
            test_dir = os.path.join(output_dir, "test")
            test_result = test_pdf_rendering(pdf_path, test_dir)
            
            if test_result["success"]:
                logger.info(f"PDF test was successful despite path check failure. Using test results.")
                # Use the test images instead
                result = {
                    "document_id": os.path.basename(output_dir),
                    "document_name": os.path.basename(pdf_path),
                    "processing_date": datetime.now().isoformat(),
                    "total_pages": len(test_result["pages"]),
                    "pages": [],
                    "fields": fields_data,
                    "test_mode": True,
                    "warning": "Using test images because normal PDF processing failed"
                }
                
                for page_data in test_result["pages"]:
                    page_num = page_data["page_number"]
                    # Copy test image to normal location
                    if page_data.get("image_path"):
                        try:
                            import shutil
                            dest_path = os.path.join(output_dir, f"page_{page_num}.png")
                            shutil.copy(page_data["image_path"], dest_path)
                            
                            # Also copy to static dir if needed
                            static_vis_dir = f"static/visualizations/{result['document_id']}"
                            if not os.path.exists(static_vis_dir):
                                os.makedirs(static_vis_dir, exist_ok=True)
                            static_path = os.path.join(static_vis_dir, f"page_{page_num}.png")
                            shutil.copy(page_data["image_path"], static_path)
                            
                            result["pages"].append({
                                "page_number": page_num,
                                "image_url": f"/static/visualizations/{result['document_id']}/page_{page_num}.png",
                                "alternate_url": f"/api/visualizations/{result['document_id']}/page_{page_num}.png",
                                "width": page_data.get("width", 0),
                                "height": page_data.get("height", 0),
                                "test_source": True
                            })
                        except Exception as copy_error:
                            logger.error(f"Error copying test image: {str(copy_error)}")
                
                return result
                
            # Create a result with error information
            error_result = {
                "document_id": os.path.basename(output_dir),
                "error": "PDF_NOT_FOUND",
                "error_message": f"PDF file not found: {pdf_path}",
                "total_pages": 0,
                "pages": [],
                "fields": fields_data
            }
            
            # Create output directory anyway for the error data
            os.makedirs(output_dir, exist_ok=True)
            static_vis_dir = os.path.join('static', 'visualizations', os.path.basename(output_dir))
            os.makedirs(static_vis_dir, exist_ok=True)
            
            # Save error metadata
            error_metadata_path = os.path.join(output_dir, "metadata.json")
            with open(error_metadata_path, "w") as f:
                json.dump(error_result, f, indent=2)
                
            return error_result
            
        logger.info(f"PDF path exists: {os.path.exists(pdf_path)}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory created: {os.path.exists(output_dir)}")
        
        # Ensure output directory exists in static/visualizations
        static_vis_dir = os.path.join('static', 'visualizations', os.path.basename(output_dir))
        os.makedirs(static_vis_dir, exist_ok=True)
        logger.info(f"Static visualization directory created: {os.path.exists(static_vis_dir)}")
        
        # Document ID is either the output_dir basename or a UUID if it's not suitable
        doc_id = os.path.basename(output_dir)
        if not doc_id or doc_id == '.' or doc_id == '..':
            doc_id = str(uuid.uuid4())
            
        logger.info(f"Using document ID: {doc_id}")
        
        result = {
            "document_id": doc_id,
            "document_name": os.path.basename(pdf_path),
            "processing_date": datetime.now().isoformat(),
            "total_pages": 0,
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
        
        logger.info(f"Processed {len(processed_fields)} fields")
        
        # Try to convert PDF pages to images
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            pages = convert_from_path(pdf_path, dpi=200)  # Higher DPI for better quality
            logger.info(f"Converted {len(pages)} pages from PDF")
            result["total_pages"] = len(pages)
            
            # Save page images and prepare visualization data
            for page_idx, page_image in enumerate(pages):
                # Save the page image
                page_number = page_idx + 1
                
                # Try PNG first, then JPEG as fallback
                image_formats = [
                    {"format": "PNG", "extension": "png"},
                    {"format": "JPEG", "extension": "jpg"}
                ]
                
                success = False
                saved_format = None
                
                for img_format in image_formats:
                    if success:
                        break
                        
                    try:
                        format_name = img_format["format"]
                        extension = img_format["extension"]
                        
                        # Save to both the regular output dir and static dir for URL access
                        image_path = os.path.join(output_dir, f"page_{page_number}.{extension}")
                        static_image_path = os.path.join(static_vis_dir, f"page_{page_number}.{extension}")
                        
                        logger.info(f"Saving page {page_number} as {format_name} to {image_path}")
                        page_image.save(image_path, format=format_name)
                        logger.info(f"Saving page {page_number} as {format_name} to {static_image_path}")
                        page_image.save(static_image_path, format=format_name)
                        
                        # Check file existence and size
                        if os.path.exists(image_path) and os.path.getsize(image_path) > 0 and \
                           os.path.exists(static_image_path) and os.path.getsize(static_image_path) > 0:
                            logger.info(f"Successfully saved {format_name} image for page {page_number}")
                            success = True
                            saved_format = img_format
                        else:
                            logger.warning(f"Saved file exists but may be empty or corrupt: {image_path}")
                    except Exception as format_error:
                        logger.error(f"Error saving page {page_number} as {format_name}: {str(format_error)}")
                
                if not success:
                    logger.error(f"Failed to save page {page_number} in any format")
                    continue
                
                # Use the successful format information
                extension = saved_format["extension"]
                
                # Add page data to result with both URL formats to ensure compatibility
                primary_url = f"/static/visualizations/{result['document_id']}/page_{page_number}.{extension}"
                backup_url = f"/api/visualizations/{result['document_id']}/page_{page_number}.{extension}"
                
                logger.info(f"Image URLs for page {page_number}: {primary_url} and {backup_url}")
                
                result["pages"].append({
                    "page_number": page_number,
                    "image_url": primary_url,
                    "alternate_url": backup_url,
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
        
        except Exception as pdf_error:
            logger.error(f"Error processing PDF file: {pdf_error}")
            # Handle PDF conversion error by using error placeholder
            result["error"] = "PDF_CONVERSION_FAILED"
            result["error_message"] = str(pdf_error)
            
            # Copy error placeholder to visualization directory
            error_img = os.path.join("static", "images", "error-placeholder.png")
            if os.path.exists(error_img):
                # If error placeholder exists, use it for visualization
                import shutil
                error_img_dest = os.path.join(static_vis_dir, "page_1.png")
                shutil.copy(error_img, error_img_dest)
                
                # Add placeholder page
                result["total_pages"] = 1
                result["pages"].append({
                    "page_number": 1,
                    "image_url": f"/api/visualizations/{result['document_id']}/page_1.png",
                    "alternate_url": f"/static/visualizations/{result['document_id']}/page_1.png",
                    "width": 800,  # Default placeholder size
                    "height": 1000,
                    "is_error_placeholder": True
                })
        
        # Add processed fields to result
        result["fields"] = processed_fields
        logger.info(f"Final result contains {len(result['fields'])} fields and {len(result['pages'])} pages")
        
        # Save visualization metadata
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"Saved visualization metadata to {metadata_path}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating field visualizations: {e}")
        # Return a minimal result with error information
        error_result = {
            "document_id": os.path.basename(output_dir) if output_dir else str(uuid.uuid4()),
            "error": "VISUALIZATION_FAILED",
            "error_message": str(e),
            "total_pages": 0,
            "pages": [],
            "fields": fields_data
        }
        
        try:
            # Try to create directories and save error metadata
            os.makedirs(output_dir, exist_ok=True)
            static_vis_dir = os.path.join('static', 'visualizations', os.path.basename(output_dir))
            os.makedirs(static_vis_dir, exist_ok=True)
            
            error_metadata_path = os.path.join(output_dir, "metadata.json")
            with open(error_metadata_path, "w") as f:
                json.dump(error_result, f, indent=2)
        except:
            # If we can't even save error metadata, just return the error result
            pass
            
        return error_result

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