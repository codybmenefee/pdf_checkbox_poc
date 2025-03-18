"""
UI components for validation and correction of form fields.
"""

import os
import logging
import json
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from typing import Dict, List, Any, Optional
import datetime

from src.config import UPLOAD_FOLDER, PROCESSED_FOLDER, TEMPLATE_FOLDER
from src.visualization import (
    get_checkbox_visualization_data, 
    export_checkbox_data, 
    save_checkbox_corrections,
    get_field_visualization_data,
    export_field_data,
    save_field_corrections,
    generate_test_document_pages,
    visualize_extracted_fields
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
ui_api = Blueprint('ui_api', __name__, template_folder='templates', static_folder='static')

@ui_api.route('/ui/templates', methods=['GET'])
def templates_ui():
    """UI for template management."""
    return render_template('templates.html')

@ui_api.route('/ui/forms', methods=['GET'])
def forms_ui():
    """UI for form management."""
    return render_template('forms.html')

@ui_api.route('/ui/validation/<form_id>', methods=['GET'])
def validation_ui(form_id):
    """UI for form validation."""
    return render_template('validation.html', form_id=form_id)

@ui_api.route('/ui/export/<form_id>', methods=['GET'])
def export_ui(form_id):
    """UI for form export."""
    return render_template('export.html', form_id=form_id)

@ui_api.route('/ui/field-visualization', methods=['GET'])
def field_visualization_ui():
    """UI for field visualization.
    
    This page allows visualizing fields on a form with their positions.
    """
    form_id = request.args.get('form_id')
    if not form_id:
        return "Error: No form ID provided", 400
    
    return render_template('field_visualization.html', form_id=form_id)

@ui_api.route('/ui/checkbox-visualization/<document_id>', methods=['GET'])
def checkbox_visualization_ui(document_id):
    """UI for checkbox detection visualization."""
    return render_template('checkbox_visualization.html', document_id=document_id)

@ui_api.route('/ui/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(ui_api.static_folder, filename)

@ui_api.route('/api/visualization/<document_id>', methods=['GET'])
def get_visualization_data(document_id):
    """API to get checkbox visualization data."""
    try:
        data = get_checkbox_visualization_data(document_id)
        if not data:
            return jsonify({"error": "Visualization data not found"}), 404
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error retrieving visualization data: {str(e)}")
        return jsonify({"error": "Failed to retrieve visualization data"}), 500

@ui_api.route('/api/field-visualization/<document_id>', methods=['GET'])
def get_field_visualization_data_api(document_id):
    """Get field visualization data for a specific document."""
    try:
        data = get_field_visualization_data(document_id)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error retrieving field visualization data: {str(e)}")
        return jsonify({
            "error": f"Failed to retrieve visualization data: {str(e)}"
        }), 500

@ui_api.route('/api/field-visualization/form/<form_id>', methods=['GET'])
def get_form_field_visualization_data(form_id):
    """Get field visualization data for a specific form.
    
    This endpoint retrieves form data including the PDF and field positions
    for visualization purposes.
    """
    logger.info(f"Visualization requested for form_id: {form_id}")
    try:
        # Retrieve form data from database
        # Using the model directly instead of the API function to avoid issues with tuple returns
        from src.db_models import FilledFormModel
        from src.db_core import DatabaseManager
        
        # Initialize database manager and model
        db_manager = DatabaseManager()
        filled_form_model = FilledFormModel(db_manager)
        
        form = filled_form_model.get(form_id)
        
        logger.info(f"Form data retrieved: {form is not None}")
        
        if form:
            logger.info(f"Form structure: {json.dumps(form, default=str)}")
        
        if not form:
            logger.error(f"Form not found: {form_id}")
            return jsonify({"error": "Form not found"}), 404
        
        # Get document data and PDF path
        document_data = form.get('document', {})
        pdf_path = os.path.join(UPLOAD_FOLDER, document_data.get('stored_filename', ''))
        logger.info(f"PDF path: {pdf_path}, exists: {os.path.exists(pdf_path)}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"Form PDF not found at path: {pdf_path}")
            return jsonify({"error": "Form PDF not found"}), 404
        
        # Use template data to get field positions
        template_id = form.get('template_id')
        logger.info(f"Template ID: {template_id}")
        from src.template_manager import TemplateManager
        template_manager = TemplateManager()
        template = template_manager.get_template(template_id)
        
        if not template:
            logger.error(f"Template not found: {template_id}")
            return jsonify({"error": "Template not found"}), 404
            
        logger.info(f"Template found with {len(template.get('fields', []))} fields")
        
        # Extract visualization data
        visualization_data = visualize_extracted_fields(pdf_path, template.get('fields', []), form_id)
        logger.info(f"Visualization data generated with {len(visualization_data.get('fields', []))} fields")
        
        return jsonify(visualization_data)
    except Exception as e:
        logger.error(f"Error retrieving form visualization data: {str(e)}")
        return jsonify({
            "error": f"Failed to retrieve form visualization data: {str(e)}"
        }), 500

@ui_api.route('/api/visualization/export', methods=['POST'])
def export_visualization_data():
    """API to export checkbox visualization data."""
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        export_data = request.json
        result = export_checkbox_data(export_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error exporting visualization data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/field-visualization/export', methods=['POST'])
def export_field_visualization_data():
    """API to export field extraction visualization data."""
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        export_data = request.json
        result = export_field_data(export_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error exporting field visualization data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/visualization/save-corrections', methods=['POST'])
def save_visualization_corrections():
    """Save manual corrections to checkboxes."""
    try:
        corrections_data = request.json
        
        if not corrections_data:
            return jsonify({"error": "No correction data provided"}), 400
        
        success = save_checkbox_corrections(corrections_data)
        
        if success:
            return jsonify({"status": "success", "message": "Corrections saved successfully"})
        else:
            return jsonify({"error": "Failed to save corrections"}), 500
    except Exception as e:
        logger.error(f"Error saving corrections: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/ui_visualizations/<visualization_id>/<path:filename>', methods=['GET'])
def serve_visualization_file(visualization_id, filename):
    """Serve visualization files from the visualization directory."""
    visualization_dir = os.path.join('static', 'visualizations', visualization_id)
    return send_from_directory(visualization_dir, filename)

@ui_api.route('/api/export/onespan', methods=['POST'])
def export_to_onespan():
    """Export a filled form to OneSpan."""
    data = request.json
    
    if not data or "form_id" not in data:
        return jsonify({"error": "Missing form_id parameter"}), 400
    
    form_id = data["form_id"]
    destination = data.get("destination", "default")
    
    try:
        # In a real implementation, this would call a service to export to OneSpan
        # For now, we'll just return success
        logger.info(f"Exporting form {form_id} to OneSpan ({destination})")
        
        # Add export record to database
        # db_api.forms.add_export_record(form_id, f"onespan:{destination}", "completed")
        
        return jsonify({
            "status": "success",
            "message": f"Form {form_id} exported to OneSpan successfully",
            "destination": destination
        })
    except Exception as e:
        logger.error(f"Error exporting to OneSpan: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/export/docusign', methods=['POST'])
def export_to_docusign():
    """Export a filled form to DocuSign."""
    data = request.json
    
    if not data or "form_id" not in data:
        return jsonify({"error": "Missing form_id parameter"}), 400
    
    form_id = data["form_id"]
    destination = data.get("destination", "default")
    
    try:
        # In a real implementation, this would call a service to export to DocuSign
        # For now, we'll just return success
        logger.info(f"Exporting form {form_id} to DocuSign ({destination})")
        
        # Add export record to database
        # db_api.forms.add_export_record(form_id, f"docusign:{destination}", "completed")
        
        return jsonify({
            "status": "success",
            "message": f"Form {form_id} exported to DocuSign successfully",
            "destination": destination
        })
    except Exception as e:
        logger.error(f"Error exporting to DocuSign: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/export/generic', methods=['POST'])
def export_generic():
    """Export a filled form to a generic destination."""
    data = request.json
    
    if not data or "form_id" not in data:
        return jsonify({"error": "Missing form_id parameter"}), 400
    
    form_id = data["form_id"]
    format = data.get("format", "pdf")
    destination = data.get("destination", "download")
    
    try:
        # In a real implementation, this would call a service to export the form
        # For now, we'll just return success
        logger.info(f"Exporting form {form_id} as {format} to {destination}")
        
        # Add export record to database
        # db_api.forms.add_export_record(form_id, f"generic:{destination}:{format}", "completed")
        
        return jsonify({
            "status": "success",
            "message": f"Form {form_id} exported successfully",
            "format": format,
            "destination": destination
        })
    except Exception as e:
        logger.error(f"Error exporting form: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/validation/corrections', methods=['POST'])
def apply_corrections():
    """Apply manual corrections to form fields."""
    data = request.json
    
    if not data or "form_id" not in data or "corrections" not in data:
        return jsonify({"error": "Missing required parameters"}), 400
    
    form_id = data["form_id"]
    corrections = data["corrections"]
    
    try:
        # In a real implementation, this would apply corrections to the database
        # For now, we'll just return success
        logger.info(f"Applying {len(corrections)} corrections to form {form_id}")
        
        return jsonify({
            "status": "success",
            "message": f"Applied {len(corrections)} corrections to form {form_id}",
            "corrections_applied": len(corrections)
        })
    except Exception as e:
        logger.error(f"Error applying corrections: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/validation/audit-log', methods=['GET'])
def get_audit_log():
    """Get audit log for form validation."""
    form_id = request.args.get("form_id")
    
    if not form_id:
        return jsonify({"error": "Missing form_id parameter"}), 400
    
    try:
        # In a real implementation, this would retrieve the audit log from the database
        # For now, we'll return a mock audit log
        audit_log = [
            {
                "timestamp": "2023-05-01T12:00:00Z",
                "user": "system",
                "action": "form_processed",
                "details": "Initial form processing completed"
            },
            {
                "timestamp": "2023-05-01T12:05:00Z",
                "user": "john.doe",
                "action": "field_corrected",
                "details": "Corrected checkbox 'option_1' from unchecked to checked"
            },
            {
                "timestamp": "2023-05-01T12:10:00Z",
                "user": "john.doe",
                "action": "form_validated",
                "details": "Form marked as validated"
            }
        ]
        
        return jsonify({
            "form_id": form_id,
            "audit_log": audit_log
        })
    except Exception as e:
        logger.error(f"Error retrieving audit log: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/field-visualization/save', methods=['POST'])
def save_field_visualization_data():
    """API to save field visualization data corrections."""
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        corrections_data = request.json
        success = save_field_corrections(corrections_data)
        
        if success:
            return jsonify({"status": "success", "message": "Field data saved successfully"})
        else:
            return jsonify({"error": "Failed to save field data"}), 500
    except Exception as e:
        logger.error(f"Error saving field visualization data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/field-visualization/generate-test-pages', methods=['POST'])
def generate_test_pages():
    """API to generate page images for a test document."""
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        data = request.json
        pdf_path = data.get('pdf_path')
        output_dir = data.get('output_dir')
        
        if not pdf_path or not output_dir:
            return jsonify({"error": "Missing required parameters: pdf_path, output_dir"}), 400
        
        # Generate page images
        page_data = generate_test_document_pages(pdf_path, output_dir)
        
        return jsonify({
            "status": "success", 
            "message": "Test document pages generated successfully",
            "pages": page_data
        })
    except Exception as e:
        logger.error(f"Error generating test document pages: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/generate-test-visualization', methods=['GET'])
def generate_test_visualization():
    """Generate a test visualization with sample fields."""
    try:
        from src.visualization import visualize_extracted_fields, generate_test_document_pages
        import os
        import uuid
        import json
        
        # Create a unique ID for this visualization
        vis_id = str(uuid.uuid4())
        output_dir = os.path.join('static', 'visualizations', vis_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Use a sample PDF file
        pdf_path = 'src/NCAF - Secured.Entity - English.pdf'
        
        # Generate some sample fields
        sample_fields = [
            {
                "id": "field1",
                "name": "New Client ID",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.126,
                    "top": 0.189,
                    "width": 0.015,
                    "height": 0.015
                },
                "value": True
            },
            {
                "id": "field2",
                "name": "Add Account",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.251,
                    "top": 0.189,
                    "width": 0.015,
                    "height": 0.015
                },
                "value": False
            },
            {
                "id": "field3",
                "name": "Update Account",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.467,
                    "top": 0.189,
                    "width": 0.015,
                    "height": 0.015
                },
                "value": False
            },
            {
                "id": "field4",
                "name": "Corporation",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.126,
                    "top": 0.230,
                    "width": 0.015,
                    "height": 0.015
                },
                "value": True
            }
        ]
        
        # Create visualization
        result = visualize_extracted_fields(pdf_path, sample_fields, output_dir)
        
        return jsonify({
            "success": True,
            "message": "Test visualization created",
            "visualization_id": vis_id,
            "visualization_url": f"/ui/field-visualization/{vis_id}"
        })
        
    except Exception as e:
        logger.error(f"Error generating test visualization: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/generate-pwl-test', methods=['GET'])
def generate_pwl_test_visualization():
    """Generate a test visualization with PWL form fields that match the screenshot."""
    try:
        from src.visualization import visualize_extracted_fields
        import os
        import uuid
        
        # Create a unique ID for this visualization
        vis_id = str(uuid.uuid4())
        output_dir = os.path.join('static', 'visualizations', vis_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Use the PWL form PDF file
        pdf_path = 'src/NCAF - Secured.Entity - English.pdf'
        
        # Define fields that match those in the screenshot
        sample_fields = [
            # Top checkboxes
            {
                "id": "new_client_id",
                "name": "New Client ID",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.134,
                    "top": 0.189,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": True
            },
            {
                "id": "add_account",
                "name": "Add Account - Existing Client ID",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.249,
                    "top": 0.189,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            {
                "id": "update_existing_account",
                "name": "Update Existing Account",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.467,
                    "top": 0.189,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            # Entity checkboxes
            {
                "id": "corporation",
                "name": "Corporation",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.230,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": True
            },
            {
                "id": "estate",
                "name": "Estate",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.249,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            {
                "id": "partnership",
                "name": "Partnership",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.267,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            {
                "id": "trust",
                "name": "Trust",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.286,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            {
                "id": "charitable_organization",
                "name": "Charitable Organization",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.304,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            {
                "id": "sole_proprietorship",
                "name": "Sole Proprietorship",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.322,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            {
                "id": "other_entity",
                "name": "Other Entity",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.132,
                    "top": 0.340,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            },
            # Non-registered checkboxes
            {
                "id": "cad",
                "name": "CAD",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.704,
                    "top": 0.231,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": True
            },
            {
                "id": "usd",
                "name": "USD",
                "type": "checkbox",
                "page": 1,
                "bbox": {
                    "left": 0.751,
                    "top": 0.231,
                    "width": 0.013,
                    "height": 0.013
                },
                "value": False
            }
        ]
        
        # Create visualization
        result = visualize_extracted_fields(pdf_path, sample_fields, output_dir)
        
        return jsonify({
            "success": True,
            "message": "PWL form test visualization created",
            "visualization_id": vis_id,
            "visualization_url": f"/ui/field-visualization/{vis_id}"
        })
        
    except Exception as e:
        logger.error(f"Error generating PWL test visualization: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/metrics/log', methods=['POST'])
def log_metrics():
    """
    Log client-side metrics for analysis.
    
    This endpoint receives metrics from the client-side JavaScript
    and stores them for later analysis.
    """
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        # Get the metric data
        metric_data = request.json
        
        # Add server timestamp
        metric_data['server_timestamp'] = datetime.datetime.utcnow().isoformat()
        
        # Log the metric data to file or database
        log_metric_to_storage(metric_data)
        
        return jsonify({"status": "success", "message": "Metric logged successfully"})
    except Exception as e:
        logger.error(f"Error logging metric: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/metrics/report', methods=['POST'])
def record_performance_report():
    """
    Record a performance report generated by the client.
    
    This endpoint receives complete performance reports that include
    aggregated statistics about the visualization session.
    """
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        # Get the report data
        report_data = request.json
        
        # Add server timestamp
        report_data['server_timestamp'] = datetime.datetime.utcnow().isoformat()
        
        # Save the report
        save_performance_report(report_data)
        
        return jsonify({"status": "success", "message": "Performance report recorded"})
    except Exception as e:
        logger.error(f"Error recording performance report: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ui_api.route('/api/template/save-field-positions', methods=['POST'])
def save_template_field_positions():
    """Save updated field positions for a template."""
    try:
        if not request.json:
            return jsonify({"error": "Invalid request - JSON body required"}), 400
            
        template_data = request.json
        template_id = template_data.get('template_id')
        fields = template_data.get('fields', [])
        version = template_data.get('version')
        
        if not template_id:
            return jsonify({"error": "Template ID is required"}), 400
            
        if not fields:
            return jsonify({"error": "No fields provided"}), 400
            
        # Load the existing template
        template_file = os.path.join(TEMPLATE_FOLDER, f"{template_id}.json")
        if not os.path.exists(template_file):
            return jsonify({"error": f"Template not found: {template_id}"}), 404
            
        with open(template_file, 'r') as f:
            template = json.load(f)
            
        # Update the fields with new positions
        template['fields'] = fields
        
        # Update version if provided
        if version:
            template['version'] = version
            template['updated_at'] = datetime.datetime.now().isoformat()
            
        # Save the updated template
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)
            
        # Create a backup of the template
        backup_dir = os.path.join(TEMPLATE_FOLDER, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f"{template_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(template, f, indent=2)
            
        logger.info(f"Saved updated field positions for template {template_id}, created backup at {backup_file}")
        
        return jsonify({
            "status": "success",
            "message": "Template field positions updated successfully",
            "version": template.get('version')
        })
        
    except Exception as e:
        logger.error(f"Error saving template field positions: {str(e)}")
        return jsonify({"error": str(e)}), 500

def log_metric_to_storage(metric_data: Dict[str, Any]) -> bool:
    """
    Log a single metric to storage.
    
    Args:
        metric_data: The metric data to log
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create metrics directory if it doesn't exist
        metrics_dir = os.path.join('data', 'metrics')
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Determine the file to log to - one file per day for easier management
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        log_file = os.path.join(metrics_dir, f'metrics_{today}.jsonl')
        
        # Append the metric to the file as a JSON line
        with open(log_file, 'a') as f:
            f.write(json.dumps(metric_data) + '\n')
            
        # Log to console for debugging
        logger.debug(f"Metric logged: {metric_data['category']} - {metric_data['action']}")
        
        return True
    except Exception as e:
        logger.error(f"Error logging metric to storage: {str(e)}")
        return False

def save_performance_report(report_data: Dict[str, Any]) -> bool:
    """
    Save a complete performance report.
    
    Args:
        report_data: The report data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join('data', 'metrics', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate a filename with session ID and timestamp
        session_id = report_data.get('sessionId', 'unknown')
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        report_file = os.path.join(reports_dir, f'report_{session_id}_{timestamp}.json')
        
        # Save the report as a JSON file
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        logger.info(f"Performance report saved: {report_file}")
        
        # Also log key metrics for easier aggregation
        metrics_summary = {
            'session_id': session_id,
            'document_id': report_data.get('documentId', 'unknown'),
            'timestamp': timestamp,
            'session_duration_ms': report_data.get('sessionDuration', 0),
            'image_loads_total': report_data.get('imageLoads', {}).get('total', 0),
            'image_loads_success_rate': report_data.get('imageLoads', {}).get('successRate', '0%'),
            'fallback_success_rate': report_data.get('imageLoads', {}).get('fallbackSuccessRate', '0%'),
            'avg_load_time_ms': report_data.get('imageLoads', {}).get('averageLoadTime', '0ms'),
            'page_changes': report_data.get('navigation', {}).get('pageChanges', 0),
            'error_count': report_data.get('errorCount', 0)
        }
        
        # Save summary to a single CSV for easier analysis
        summary_file = os.path.join(reports_dir, 'reports_summary.csv')
        file_exists = os.path.exists(summary_file)
        
        with open(summary_file, 'a') as f:
            # Write header if the file is new
            if not file_exists:
                header = ','.join(metrics_summary.keys())
                f.write(header + '\n')
                
            # Write values
            values = ','.join(str(v) for v in metrics_summary.values())
            f.write(values + '\n')
        
        return True
    except Exception as e:
        logger.error(f"Error saving performance report: {str(e)}")
        return False
