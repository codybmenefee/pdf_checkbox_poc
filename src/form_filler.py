"""
Form filling module for applying templates to PDF documents.
"""

import os
import logging
import uuid
from typing import Dict, List, Any, Optional
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import json

from src.config import PROCESSED_FOLDER, TEMPLATE_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormFiller:
    """Handler for filling PDF forms with checkbox data."""
    
    def __init__(self):
        """Initialize the form filler."""
        logger.info("Initialized Form Filler")
    
    def apply_template(self, template_data: Dict[str, Any], pdf_path: str, 
                      field_values: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Apply a template to a PDF document.
        
        Args:
            template_data: Template data
            pdf_path: Path to the PDF file
            field_values: Optional list of field values to override template defaults
            
        Returns:
            Path to the filled PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Generate a unique ID for the filled form
        filled_form_id = str(uuid.uuid4())
        
        # Create output path
        output_dir = os.path.join(PROCESSED_FOLDER, "filled")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"filled_{filled_form_id}.pdf")
        
        # Create a mapping of field_id to value
        field_value_map = {}
        if field_values:
            for field_value in field_values:
                if "field_id" in field_value and "value" in field_value:
                    field_value_map[field_value["field_id"]] = field_value["value"]
        
        # Process each field in the template
        fields = template_data.get("fields", [])
        
        # Group fields by page
        fields_by_page = {}
        for field in fields:
            page = field.get("page", 1)
            if page not in fields_by_page:
                fields_by_page[page] = []
            fields_by_page[page].append(field)
        
        # Open the input PDF
        with open(pdf_path, "rb") as input_file:
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            # Process each page
            for page_num in range(len(reader.pages)):
                # Get the page
                page = reader.pages[page_num]
                
                # Check if we have fields for this page
                page_number = page_num + 1  # 1-based page numbering
                if page_number in fields_by_page:
                    # Create a new PDF with checkboxes for this page
                    checkbox_pdf = self._create_checkbox_overlay(
                        fields_by_page[page_number],
                        field_value_map,
                        page.mediabox.width,
                        page.mediabox.height
                    )
                    
                    # Merge the checkbox PDF with the original page
                    checkbox_reader = PdfReader(BytesIO(checkbox_pdf))
                    checkbox_page = checkbox_reader.pages[0]
                    
                    # Merge the pages
                    page.merge_page(checkbox_page)
                
                # Add the page to the output PDF
                writer.add_page(page)
            
            # Write the output PDF
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
        
        logger.info(f"Created filled PDF: {output_path}")
        
        return output_path
    
    def _create_checkbox_overlay(self, fields: List[Dict[str, Any]], 
                                field_value_map: Dict[str, bool],
                                width: float, height: float) -> bytes:
        """
        Create a PDF overlay with checkboxes.
        
        Args:
            fields: List of fields to add to the overlay
            field_value_map: Mapping of field_id to value
            width: Page width
            height: Page height
            
        Returns:
            PDF data as bytes
        """
        # Create a new PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(width, height))
        
        # Draw checkboxes
        for field in fields:
            field_id = field.get("field_id", "")
            field_type = field.get("field_type", "")
            
            # Only process checkbox fields
            if field_type != "checkbox":
                continue
            
            # Get the field value (checked or unchecked)
            is_checked = field_value_map.get(field_id, field.get("default_value", False))
            
            # Get the coordinates
            coordinates = field.get("coordinates", {})
            vertices = coordinates.get("vertices", [])
            
            if not vertices or len(vertices) < 4:
                logger.warning(f"Invalid vertices for field: {field_id}")
                continue
            
            # Calculate the bounding box
            x_coords = [vertex.get("x", 0) for vertex in vertices]
            y_coords = [vertex.get("y", 0) for vertex in vertices]
            
            x_min = min(x_coords)
            y_min = min(y_coords)
            x_max = max(x_coords)
            y_max = max(y_coords)
            
            # Adjust y-coordinates (PDF coordinates start from bottom)
            y_min = height - y_max
            y_max = height - y_min
            
            # Draw the checkbox
            if is_checked:
                self._draw_checked_box(c, x_min, y_min, x_max, y_max)
            
        # Save the canvas
        c.save()
        
        # Get the PDF data
        buffer.seek(0)
        return buffer.getvalue()
    
    def _draw_checked_box(self, canvas, x_min, y_min, x_max, y_max):
        """
        Draw a checked checkbox on the canvas.
        
        Args:
            canvas: ReportLab canvas
            x_min: Minimum x coordinate
            y_min: Minimum y coordinate
            x_max: Maximum x coordinate
            y_max: Maximum y coordinate
        """
        # Calculate dimensions
        width = x_max - x_min
        height = y_max - y_min
        
        # Draw an X
        canvas.setStrokeColorRGB(0, 0, 0)  # Black
        canvas.setLineWidth(2)
        
        # Draw first diagonal
        canvas.line(x_min, y_min, x_max, y_max)
        
        # Draw second diagonal
        canvas.line(x_min, y_max, x_max, y_min)


class FieldMapper:
    """Handler for mapping fields between templates and documents."""
    
    def __init__(self):
        """Initialize the field mapper."""
        logger.info("Initialized Field Mapper")
    
    def map_template_to_document(self, template_data: Dict[str, Any], 
                                target_document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map template fields to a target document.
        
        Args:
            template_data: Template data
            target_document_data: Target document data
            
        Returns:
            Mapping data
        """
        # Extract template fields
        template_fields = template_data.get("fields", [])
        
        # Create mapping
        mapping = {
            "template_id": template_data.get("template_id", ""),
            "target_document": {
                "original_filename": target_document_data.get("original_filename", ""),
                "file_size": target_document_data.get("file_size", 0),
                "page_count": len(target_document_data.get("pages", [])),
            },
            "field_mappings": []
        }
        
        # Map each field
        for field in template_fields:
            field_id = field.get("field_id", "")
            field_type = field.get("field_type", "")
            label = field.get("label", "")
            page = field.get("page", 1)
            
            # Create field mapping
            field_mapping = {
                "field_id": field_id,
                "field_type": field_type,
                "label": label,
                "page": page,
                "source_coordinates": field.get("coordinates", {}),
                "target_coordinates": field.get("coordinates", {}),  # Default to same coordinates
                "confidence": 1.0  # Default confidence
            }
            
            mapping["field_mappings"].append(field_mapping)
        
        return mapping
    
    def adjust_mapping_scale(self, mapping_data: Dict[str, Any], 
                           source_dimensions: Dict[str, float],
                           target_dimensions: Dict[str, float]) -> Dict[str, Any]:
        """
        Adjust mapping scale based on document dimensions.
        
        Args:
            mapping_data: Mapping data
            source_dimensions: Source document dimensions
            target_dimensions: Target document dimensions
            
        Returns:
            Adjusted mapping data
        """
        # Calculate scale factors
        scale_x = target_dimensions.get("width", 1) / source_dimensions.get("width", 1)
        scale_y = target_dimensions.get("height", 1) / source_dimensions.get("height", 1)
        
        # Adjust each field mapping
        for field_mapping in mapping_data.get("field_mappings", []):
            source_coords = field_mapping.get("source_coordinates", {})
            target_coords = field_mapping.get("target_coordinates", {})
            
            # Adjust vertices
            if "vertices" in source_coords:
                target_vertices = []
                for vertex in source_coords.get("vertices", []):
                    target_vertex = {
                        "x": vertex.get("x", 0) * scale_x,
                        "y": vertex.get("y", 0) * scale_y
                    }
                    target_vertices.append(target_vertex)
                
                target_coords["vertices"] = target_vertices
            
            # Adjust normalized vertices (no need to scale these)
            if "normalized_vertices" in source_coords:
                target_coords["normalized_vertices"] = source_coords.get("normalized_vertices", [])
            
            field_mapping["target_coordinates"] = target_coords
        
        return mapping_data
