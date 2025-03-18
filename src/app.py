"""
Main application with integrated UI API.
"""

import os
from dotenv import load_dotenv
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template
import json
import uuid
from datetime import datetime

# Configure logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables at startup
logger.debug("Loading environment variables in app.py...")
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
logger.debug(f"Looking for .env file at: {env_path}")
logger.debug(f"File exists: {os.path.exists(env_path)}")

# Force set environment variables from .env
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
                logger.debug(f"Manually set {key}={value}")

# Log loaded environment variables
logger.debug("Loaded environment variables:")
logger.debug(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")
logger.debug(f"GCP_LOCATION: {os.environ.get('GCP_LOCATION')}")
logger.debug(f"GCP_PROCESSOR_ID: {os.environ.get('GCP_PROCESSOR_ID')}")

# Import components after environment variables are loaded
from src.config import UPLOAD_FOLDER, PROCESSED_FOLDER, TEMPLATE_FOLDER
from src.document_ai_client import DocumentAIClient
from src.pdf_handler import PDFHandler
from src.template_manager import TemplateManager
from src.db_api import db_api
from src.form_api import form_api, fill_form
from src.ui_api import ui_api
from src.visualization import visualize_template, visualize_checkboxes_with_confidence, visualize_extracted_fields

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Initialize components
document_ai_client = DocumentAIClient()
pdf_handler = PDFHandler(document_ai_client)
template_manager = TemplateManager()

# Register blueprints
app.register_blueprint(db_api)
app.register_blueprint(form_api)
app.register_blueprint(ui_api)

@app.route('/')
def index():
    """Redirect to templates UI."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "PDF Checkbox Extraction & Form Filling System is running"})

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Upload a PDF document."""
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Upload the file
        file_info = pdf_handler.upload_pdf(file)
        return jsonify({"message": "File uploaded successfully", "file_info": file_info})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/documents/<file_id>/process', methods=['POST'])
def process_document(file_id):
    """Process a document with Document AI."""
    # Find the file
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.startswith(f"{file_id}_"):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file_info = {
                "file_id": file_id,
                "original_filename": filename.replace(f"{file_id}_", ""),
                "stored_filename": filename,
                "file_path": file_path,
                "file_size": os.path.getsize(file_path)
            }
            
            try:
                # Process the document
                result = pdf_handler.process_pdf(file_info)
                
                # Load the processed document data
                processed_path = os.path.join(PROCESSED_FOLDER, f"processed_{file_id}.json")
                with open(processed_path, 'r') as f:
                    document_data = json.load(f)
                
                # Extract form fields
                fields = pdf_handler.extract_form_fields(document_data)
                
                # Count checkboxes (fields with type 'checkbox')
                checkboxes = [f for f in fields if f.get("field_type") == "checkbox"]
                
                return jsonify({
                    "message": "Document processed successfully",
                    "file_id": file_id,
                    "fields_count": len(fields),
                    "checkboxes_count": len(checkboxes),
                    "fields": fields
                })
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                return jsonify({"error": "Error processing document"}), 500
    
    return jsonify({"error": "File not found"}), 404

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Create a new template from processed document data."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ["name", "description", "file_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Find the processed document data
    processed_path = os.path.join(PROCESSED_FOLDER, f"processed_{data['file_id']}.json")
    if not os.path.exists(processed_path):
        return jsonify({"error": "Processed document data not found"}), 404
    
    try:
        # Load the processed document data
        with open(processed_path, 'r') as f:
            document_data = json.load(f)
        
        # Extract form fields
        fields = pdf_handler.extract_form_fields(document_data)
        
        # Create the template
        template = template_manager.create_template(
            name=data["name"],
            description=data["description"],
            document_data=document_data,
            fields=fields,
            tags=data.get("tags", [])
        )
        
        return jsonify({
            "message": "Template created successfully",
            "template_id": template["template_id"],
            "fields_count": len(template["fields"])
        })
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return jsonify({"error": "Error creating template"}), 500

@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List all templates."""
    try:
        # Get tags from query parameters
        tags = request.args.get('tags')
        tags_list = tags.split(',') if tags else None
        
        # List templates
        templates = template_manager.list_templates(tags=tags_list)
        
        # Return simplified template list
        template_list = []
        for template in templates:
            template_list.append({
                "template_id": template["template_id"],
                "name": template["name"],
                "description": template["description"],
                "created_at": template["created_at"],
                "updated_at": template["updated_at"],
                "tags": template["tags"],
                "version": template["version"],
                "fields_count": len(template["fields"])
            })
        
        return jsonify({"templates": template_list})
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        return jsonify({"error": "Error listing templates"}), 500

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a template by ID."""
    try:
        # Get the template
        template = template_manager.get_template(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({"template": template})
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        return jsonify({"error": "Error getting template"}), 500

@app.route('/api/templates/<template_id>/visualize', methods=['GET'])
def visualize_template_fields(template_id):
    """Generate visualization of template fields overlaid on the PDF."""
    try:
        # Get the template
        template = template_manager.get_template(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Find the original PDF file
        pdf_filename = None
        original_filename = template["document"]["original_filename"]
        
        # First try to find by original filename
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith(original_filename):
                pdf_filename = filename
                break
        
        # If not found, try to find by processed data
        if not pdf_filename:
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.endswith('.pdf'):
                    # Load the processed data to check file_id
                    processed_path = os.path.join(PROCESSED_FOLDER, f"processed_{filename.split('_')[0]}.json")
                    if os.path.exists(processed_path):
                        with open(processed_path, 'r') as f:
                            processed_data = json.load(f)
                            if processed_data.get("original_filename") == original_filename:
                                pdf_filename = filename
                                break
        
        if not pdf_filename:
            return jsonify({"error": "Original PDF not found"}), 404
        
        # Create visualization directory
        vis_dir = os.path.join(app.static_folder, 'visualizations', template_id)
        os.makedirs(vis_dir, exist_ok=True)
        
        # Generate visualizations
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        visualization_paths = visualize_template(pdf_path, template, vis_dir)
        
        # Convert paths to URLs
        visualization_urls = [
            f"/static/visualizations/{template_id}/{os.path.basename(path)}"
            for path in visualization_paths
        ]
        
        return jsonify({
            "message": "Visualization generated successfully",
            "template_id": template_id,
            "pages": visualization_urls
        })
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return jsonify({"error": "Error generating visualization"}), 500

@app.route('/api/documents/<file_id>/visualize-checkboxes', methods=['POST'])
def visualize_document_checkboxes(file_id):
    """Process a document for checkbox visualization with confidence scores."""
    try:
        # Get document path
        document_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(document_path):
            return jsonify({"error": f"Document {file_id} not found"}), 404
            
        # Get confidence thresholds from request
        data = request.json or {}
        high_confidence_threshold = data.get('high_confidence_threshold', 0.9)
        medium_confidence_threshold = data.get('medium_confidence_threshold', 0.7)
        
        # Create visualization ID (using document ID for simplicity)
        visualization_id = file_id
        
        # Create output directory
        output_dir = os.path.join(PROCESSED_FOLDER, "visualizations", visualization_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Process document with Document AI
        client = DocumentAIClient()
        result = client.process_document(document_path)
        
        # Extract checkboxes with confidence scores
        checkboxes = []
        for page_idx, page in enumerate(result.get('pages', [])):
            page_checkboxes = page.get('checkboxes', [])
            for checkbox in page_checkboxes:
                # Add page number (1-indexed)
                checkbox['page'] = page_idx + 1
                
                # Generate a unique ID for the checkbox
                checkbox['id'] = str(uuid.uuid4())
                
                # Add to list
                checkboxes.append(checkbox)
        
        # Create visualizations
        visualization_data = visualize_checkboxes_with_confidence(
            document_path,
            checkboxes,
            output_dir,
            high_confidence_threshold,
            medium_confidence_threshold
        )
        
        return jsonify({
            "status": "success",
            "message": "Document processed for checkbox visualization",
            "visualization_id": visualization_id,
            "visualization_url": f"/ui/checkbox-visualization/{visualization_id}"
        })
        
    except Exception as e:
        logger.error(f"Error processing document for visualization: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<file_id>/visualize-fields', methods=['POST'])
def visualize_document_fields(file_id):
    """Visualize extracted fields in a document."""
    try:
        # Check if document exists
        query = "SELECT filename FROM documents WHERE id = %s"
        result = db_query(query, (file_id,))
        
        if not result or not result[0]:
            return jsonify({"error": "Document not found"}), 404
            
        pdf_filename = result[0][0]
        
        # Get fields data from request
        if not request.json:
            return jsonify({"error": "Request body must be JSON"}), 400
            
        fields_data = request.json.get("fields", [])
        
        if not fields_data:
            return jsonify({"error": "No field data provided"}), 400
        
        # Create visualization directory with unique ID
        visualization_id = str(uuid.uuid4())
        vis_dir = os.path.join(app.static_folder, 'visualizations', visualization_id)
        os.makedirs(vis_dir, exist_ok=True)
        
        # Generate visualizations
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        visualization_data = visualize_extracted_fields(pdf_path, fields_data, vis_dir)
        
        return jsonify({
            "message": "Field visualization generated successfully",
            "visualization_id": visualization_id,
            "visualization_url": f"/ui/field-visualization/{visualization_id}"
        })
        
    except Exception as e:
        app.logger.error(f"Error visualizing fields: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template by ID."""
    try:
        # Delete the template
        success = template_manager.delete_template(template_id)
        
        if not success:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({"message": "Template deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        return jsonify({"error": "Error deleting template"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
