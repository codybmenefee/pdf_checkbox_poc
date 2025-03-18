"""
API endpoints for form filling and field mapping.
"""

import os
import logging
from flask import Blueprint, request, jsonify, send_file
from typing import Dict, List, Any, Optional

from src.form_filler import FormFiller, FieldMapper
from src.database import TemplateModel, FilledFormModel, DatabaseManager
from src.config import UPLOAD_FOLDER, PROCESSED_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
form_api = Blueprint('form_api', __name__)

# Initialize components
form_filler = FormFiller()
field_mapper = FieldMapper()
db_manager = DatabaseManager()
template_model = TemplateModel(db_manager)
filled_form_model = FilledFormModel(db_manager)

@form_api.route('/api/forms/fill', methods=['POST'])
def fill_form():
    """Fill a form using a template."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ["template_id", "pdf_file_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        # Get the template
        template = template_model.get(data["template_id"])
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Find the PDF file
        pdf_path = None
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(f"{data['pdf_file_id']}_"):
                pdf_path = os.path.join(UPLOAD_FOLDER, filename)
                break
        
        if not pdf_path:
            return jsonify({"error": "PDF file not found"}), 404
        
        # Get field values if provided
        field_values = data.get("field_values", None)
        
        # Apply the template to the PDF
        filled_pdf_path = form_filler.apply_template(
            template_data=template,
            pdf_path=pdf_path,
            field_values=field_values
        )
        
        # Create a filled form record in the database
        document_info = {
            "original_filename": os.path.basename(pdf_path),
            "file_size": os.path.getsize(pdf_path),
            "filled_path": filled_pdf_path
        }
        
        # Use provided field values or default values from template
        if not field_values:
            field_values = []
            for field in template.get("fields", []):
                field_values.append({
                    "field_id": field.get("field_id", ""),
                    "value": field.get("default_value", False)
                })
        
        filled_form = filled_form_model.create(
            template_id=data["template_id"],
            name=data.get("name", f"Filled Form - {os.path.basename(pdf_path)}"),
            document_info=document_info,
            field_values=field_values
        )
        
        return jsonify({
            "message": "Form filled successfully",
            "form_id": filled_form["form_id"],
            "filled_pdf_path": filled_pdf_path
        })
    except Exception as e:
        logger.error(f"Error filling form: {str(e)}")
        return jsonify({"error": f"Error filling form: {str(e)}"}), 500

@form_api.route('/api/forms/<form_id>/download', methods=['GET'])
def download_filled_form(form_id):
    """Download a filled form."""
    try:
        # Get the filled form
        filled_form = filled_form_model.get(form_id)
        if not filled_form:
            return jsonify({"error": "Filled form not found"}), 404
        
        # Get the filled PDF path
        filled_pdf_path = filled_form.get("document", {}).get("filled_path")
        if not filled_pdf_path or not os.path.exists(filled_pdf_path):
            return jsonify({"error": "Filled PDF not found"}), 404
        
        # Return the file
        return send_file(
            filled_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"filled_form_{form_id}.pdf"
        )
    except Exception as e:
        logger.error(f"Error downloading filled form: {str(e)}")
        return jsonify({"error": f"Error downloading filled form: {str(e)}"}), 500

@form_api.route('/api/forms/map', methods=['POST'])
def map_template_to_document():
    """Map a template to a document."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ["template_id", "target_document_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        # Get the template
        template = template_model.get(data["template_id"])
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Find the target document data
        target_document_path = os.path.join(
            PROCESSED_FOLDER, 
            f"processed_{data['target_document_id']}.json"
        )
        
        if not os.path.exists(target_document_path):
            return jsonify({"error": "Target document data not found"}), 404
        
        # Load the target document data
        with open(target_document_path, 'r') as f:
            import json
            target_document_data = json.load(f)
        
        # Map the template to the target document
        mapping = field_mapper.map_template_to_document(
            template_data=template,
            target_document_data=target_document_data
        )
        
        # Adjust mapping scale if dimensions are provided
        if "source_dimensions" in data and "target_dimensions" in data:
            mapping = field_mapper.adjust_mapping_scale(
                mapping_data=mapping,
                source_dimensions=data["source_dimensions"],
                target_dimensions=data["target_dimensions"]
            )
        
        return jsonify({
            "message": "Template mapped to document successfully",
            "mapping": mapping
        })
    except Exception as e:
        logger.error(f"Error mapping template to document: {str(e)}")
        return jsonify({"error": f"Error mapping template to document: {str(e)}"}), 500

@form_api.route('/api/forms/validate', methods=['POST'])
def validate_field_mapping():
    """Validate field mapping."""
    data = request.json
    
    if not data or "mapping" not in data:
        return jsonify({"error": "No mapping data provided"}), 400
    
    try:
        # Perform validation checks
        mapping = data["mapping"]
        field_mappings = mapping.get("field_mappings", [])
        
        validation_results = []
        for field_mapping in field_mappings:
            field_id = field_mapping.get("field_id", "")
            
            # Check if target coordinates are valid
            target_coords = field_mapping.get("target_coordinates", {})
            vertices = target_coords.get("vertices", [])
            
            is_valid = len(vertices) >= 4
            
            validation_result = {
                "field_id": field_id,
                "is_valid": is_valid,
                "issues": [] if is_valid else ["Invalid target coordinates"]
            }
            
            validation_results.append(validation_result)
        
        # Overall validation result
        is_valid = all(result["is_valid"] for result in validation_results)
        
        return jsonify({
            "is_valid": is_valid,
            "field_validations": validation_results
        })
    except Exception as e:
        logger.error(f"Error validating field mapping: {str(e)}")
        return jsonify({"error": f"Error validating field mapping: {str(e)}"}), 500
