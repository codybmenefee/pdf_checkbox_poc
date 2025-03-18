"""
Main application with integrated UI API.
"""

import os
from dotenv import load_dotenv
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
import json
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import argparse
import traceback
import shutil

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

# Ensure static folder is properly set
static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
# Explicitly set the app's static folder to our custom path
app.static_folder = static_folder
app.static_url_path = '/static'  # Ensure consistent URL path

if not os.path.exists(static_folder):
    os.makedirs(static_folder, exist_ok=True)
    logger.info(f"Created static folder at {static_folder}")

# Create placeholder folders in static
visualizations_dir = os.path.join(static_folder, "visualizations")
images_dir = os.path.join(static_folder, "images")
os.makedirs(visualizations_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)

# Log static folder configuration for debugging
logger.info(f"Using static folder at: {static_folder}")
logger.info(f"Static URL path: {app.static_url_path}")

# Function to ensure static files from src/static are copied to app.static_folder
def sync_static_folders():
    """Sync files from src/static to the app's configured static folder."""
    src_static = os.path.join(os.path.dirname(__file__), 'static')
    
    if os.path.exists(src_static) and os.path.isdir(src_static):
        logger.info(f"Syncing static files from {src_static} to {static_folder}")
        
        # Walk through src/static directory and copy files to app.static_folder
        for root, dirs, files in os.walk(src_static):
            # Get relative path from src/static
            rel_path = os.path.relpath(root, src_static)
            if rel_path == '.':
                rel_path = ''
                
            # Create corresponding directory in app.static_folder if it doesn't exist
            target_dir = os.path.join(static_folder, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy each file if it doesn't exist or is newer in src/static
            for file in files:
                src_file = os.path.join(root, file)
                target_file = os.path.join(target_dir, file)
                
                # Copy file if it doesn't exist in target or if source is newer
                if not os.path.exists(target_file) or os.path.getmtime(src_file) > os.path.getmtime(target_file):
                    logger.debug(f"Copying {src_file} to {target_file}")
                    try:
                        shutil.copy2(src_file, target_file)
                    except Exception as e:
                        logger.error(f"Error copying {src_file} to {target_file}: {str(e)}")

# Sync static folders on startup
sync_static_folders()

# Check for placeholder images and create if needed
error_placeholder = os.path.join(images_dir, "error-placeholder.png")
loading_placeholder = os.path.join(images_dir, "loading-placeholder.png")

if not os.path.exists(error_placeholder) or not os.path.exists(loading_placeholder):
    # Create simple placeholder images if they don't exist
    try:
        # Create error placeholder
        error_img = Image.new('RGB', (800, 600), color='#ffcccc')
        draw = ImageDraw.Draw(error_img)
        draw.text((400, 300), "Error loading document", fill='#ff0000')
        error_img.save(error_placeholder)
        
        # Create loading placeholder
        loading_img = Image.new('RGB', (800, 600), color='#f5f5f5')
        draw = ImageDraw.Draw(loading_img)
        draw.text((400, 300), "Loading document...", fill='#333333')
        loading_img.save(loading_placeholder)
        
        logger.info("Created placeholder images for visualization")
    except Exception as e:
        logger.error(f"Error creating placeholder images: {str(e)}")

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
        logger.info(f"Visualizing template: {template_id}")
        # Get the template
        template = template_manager.get_template(template_id)
        
        if not template:
            logger.error(f"Template not found: {template_id}")
            return jsonify({"error": "Template not found"}), 404
            
        # Log template info for debugging
        logger.info(f"Template found: {template.get('name')}, fields: {len(template.get('fields', []))}")
        
        # Check if we want to paginate results
        page = request.args.get('page', type=int)
        
        # Find the original PDF file
        pdf_filename = None
        original_filename = template["document"]["original_filename"]
        file_id = template["document"].get("file_id")
        stored_filename = template["document"].get("stored_filename")
        
        logger.info(f"Looking for document: original={original_filename}, stored={stored_filename}, id={file_id}")
        
        # Try multiple approaches to find the PDF
        pdf_paths_to_try = []
        
        # 1. Try stored filename if available
        if stored_filename:
            pdf_paths_to_try.append(os.path.join(UPLOAD_FOLDER, stored_filename))
            
        # 2. Try by file_id
        if file_id:
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.startswith(f"{file_id}_"):
                    pdf_paths_to_try.append(os.path.join(UPLOAD_FOLDER, filename))
                    
        # 3. Try by original filename
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith(original_filename):
                pdf_paths_to_try.append(os.path.join(UPLOAD_FOLDER, filename))
                
        # Find first valid PDF path
        pdf_path = None
        for path in pdf_paths_to_try:
            if os.path.exists(path):
                pdf_path = path
                logger.info(f"Found PDF file at: {pdf_path}")
                break
                
        if not pdf_path:
            logger.warning(f"PDF file not found for template {template_id}")
            # Create visualization dir anyway
            visualization_dir = os.path.join(PROCESSED_FOLDER, "visualizations", template_id)
            os.makedirs(visualization_dir, exist_ok=True)
            static_vis_dir = os.path.join("static", "visualizations", template_id)
            os.makedirs(static_vis_dir, exist_ok=True)
            
            # Return error placeholder image
            error_img = os.path.join(static_folder, "images", "error-placeholder.png")
            error_img_dest = os.path.join(static_vis_dir, "page_1.png")
            if os.path.exists(error_img):
                import shutil
                shutil.copy(error_img, error_img_dest)
                
            return jsonify({
                "pages": [
                    {
                        "page_number": 1,
                        "image_url": f"/static/visualizations/{template_id}/page_1.png",
                        "alternate_url": f"/static/images/error-placeholder.png",
                        "width": 800,
                        "height": 600,
                        "error": "PDF file not found"
                    }
                ]
            })
        
        # Generate visualization
        visualization_dir = os.path.join(PROCESSED_FOLDER, "visualizations", template_id)
        
        # Create static symlink directory for web access
        static_vis_dir = os.path.join("static", "visualizations", template_id)
        os.makedirs(static_vis_dir, exist_ok=True)
        
        # Check if visualization already exists
        if os.path.exists(visualization_dir):
            page_files = [f for f in os.listdir(visualization_dir) if f.startswith("page_") and (f.endswith(".png") or f.endswith(".jpg"))]
            
            # If files exist and we're not forcing regeneration, use existing files
            if page_files and not request.args.get('regenerate'):
                logger.info(f"Using existing visualization files in {visualization_dir}")
                pages = []
                
                for filename in sorted(page_files):
                    if filename.startswith("page_") and (filename.endswith(".png") or filename.endswith(".jpg")):
                        page_num = int(filename.replace("page_", "").replace(".png", "").replace(".jpg", ""))
                        
                        # Copy to static dir if needed
                        source_path = os.path.join(visualization_dir, filename)
                        static_path = os.path.join(static_vis_dir, filename)
                        
                        if not os.path.exists(static_path):
                            logger.info(f"Copying {source_path} to {static_path}")
                            import shutil
                            shutil.copy(source_path, static_path)
                        
                        pages.append({
                            "page_number": page_num,
                            "image_url": f"/static/visualizations/{template_id}/{filename}",
                            "alternate_url": f"/api/visualizations/{template_id}/{filename}"
                        })
                
                if page:
                    # Return only the requested page
                    matching_page = next((p for p in pages if p["page_number"] == page), None)
                    if matching_page:
                        return jsonify({"pages": [matching_page]})
                    else:
                        return jsonify({"error": f"Page {page} not found"}), 404
                
                return jsonify({"pages": pages})
        
        # Need to regenerate visualizations
        try:
            # First try to use the enhanced visualization that provides separate images and field data
            logger.info(f"Generating visualization for template {template_id} from {pdf_path}")
            visualization_data = visualize_extracted_fields(
                pdf_path=pdf_path,
                fields_data=template["fields"],
                output_dir=visualization_dir
            )
            
            # Make sure static files exist
            for page_data in visualization_data["pages"]:
                # Check for static file and create if needed
                for img_url in [page_data.get("image_url"), page_data.get("alternate_url")]:
                    if img_url and img_url.startswith("/static/"):
                        # Extract the filename
                        filename = os.path.basename(img_url)
                        source_dir = os.path.dirname(img_url).replace("/static/", "")
                        
                        # Make sure the file exists in static
                        absolute_static_path = os.path.join(static_folder, source_dir, filename)
                        if not os.path.exists(absolute_static_path) and os.path.exists(os.path.join(visualization_dir, filename)):
                            # Copy from visualization dir to static
                            os.makedirs(os.path.dirname(absolute_static_path), exist_ok=True)
                            import shutil
                            shutil.copy(os.path.join(visualization_dir, filename), absolute_static_path)
            
            if page:
                # Return only the requested page
                matching_page = next((p for p in visualization_data["pages"] if p["page_number"] == page), None)
                if matching_page:
                    return jsonify({"pages": [matching_page]})
                else:
                    return jsonify({"error": f"Page {page} not found"}), 404
            
            return jsonify({"pages": visualization_data["pages"]})
        
        except Exception as e:
            logger.error(f"Error generating enhanced visualization: {str(e)}")
            
            # Fall back to the original visualization method if enhanced fails
            try:
                # Call original visualization function as fallback
                visualization_paths = visualize_template(
                    pdf_path=pdf_path,
                    template_data=template,
                    output_dir=visualization_dir
                )
                
                # Copy files to static directory for web access
                pages = []
                for i, vis_path in enumerate(visualization_paths):
                    page_num = i + 1
                    filename = f"visualization_page_{page_num}.png"
                    static_path = os.path.join(static_vis_dir, filename)
                    
                    # Copy file to static directory
                    with open(vis_path, 'rb') as f_src:
                        with open(static_path, 'wb') as f_dst:
                            f_dst.write(f_src.read())
                    
                    pages.append({
                        "page_number": page_num,
                        "image_url": f"/static/visualizations/{template_id}/{filename}"
                    })
                
                if page:
                    # Return only the requested page
                    matching_page = next((p for p in pages if p["page_number"] == page), None)
                    if matching_page:
                        return jsonify({"pages": [matching_page]})
                    else:
                        return jsonify({"error": f"Page {page} not found"}), 404
                
                return jsonify({"pages": pages})
            except Exception as e:
                logger.error(f"Error generating fallback visualization: {str(e)}")
                return jsonify({"error": f"Error generating visualization: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Error in template visualization: {str(e)}")
        return jsonify({"error": f"Error generating visualization: {str(e)}"}), 500

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

@app.route('/static/visualizations/<visualization_id>/<path:filename>', methods=['GET'])
def serve_static_visualization(visualization_id, filename):
    """Serve static visualization files, checking multiple possible locations."""
    logger.debug(f"Serving static visualization: {visualization_id}/{filename}")
    
    # Define potential locations in order of preference
    potential_paths = [
        os.path.join(app.static_folder, 'visualizations', visualization_id),
        os.path.join(os.getcwd(), 'static', 'visualizations', visualization_id),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'visualizations', visualization_id),
        os.path.join(PROCESSED_FOLDER, 'visualizations', visualization_id),
        os.path.join(UPLOAD_FOLDER, visualization_id)
    ]
    
    # Try each potential path
    for path in potential_paths:
        file_path = os.path.join(path, filename)
        logger.debug(f"Checking path: {file_path}")
        if os.path.exists(file_path) and os.path.isfile(file_path):
            logger.debug(f"Found visualization file at: {file_path}")
            return send_file(file_path)
    
    logger.warning(f"Visualization file not found: {visualization_id}/{filename}")
    return "File not found", 404

@app.route('/ui/templates/visualize', methods=['GET'])
def template_visualization():
    """Advanced template field visualization UI."""
    return render_template('template_advanced_visualization.html')

@app.route('/api/visualizations/<visualization_id>/<path:filename>', methods=['GET'])
def serve_visualization(visualization_id, filename):
    """Serve visualization files directly from the API."""
    print(f"=== SERVE_VISUALIZATION CALLED: {visualization_id}/{filename} ===")
    logger.debug(f"Serving visualization via API: {visualization_id}/{filename}")
    logger.debug(f"Current app.static_folder: {app.static_folder}")
    
    # Define all possible paths in order of preference
    potential_paths = [
        os.path.join(app.static_folder, "visualizations", visualization_id, filename),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "visualizations", visualization_id, filename),
        os.path.join(os.getcwd(), "static", "visualizations", visualization_id, filename),
        os.path.join(PROCESSED_FOLDER, "visualizations", visualization_id, filename)
    ]
    
    # Try each potential path
    for path in potential_paths:
        logger.debug(f"Checking path: {path}")
        if os.path.exists(path) and os.path.isfile(path):
            logger.debug(f"Found visualization file at: {path}")
            return send_file(path)
    
    logger.warning(f"API visualization file not found: {visualization_id}/{filename}")
    return jsonify({"error": f"Visualization file {filename} not found"}), 404

# Add debug routes for checking static file access
@app.route('/static_debug', methods=['GET'])
def static_debug():
    """Debug endpoint for checking static files."""
    result = {
        "static_folder": static_folder,
        "exists": os.path.exists(static_folder),
        "contents": {}
    }
    
    # List contents of static folder
    if os.path.exists(static_folder):
        for root, dirs, files in os.walk(static_folder):
            rel_path = os.path.relpath(root, static_folder)
            if rel_path == '.':
                rel_path = ''
            path_info = {"files": [], "dirs": []}
            for file in files:
                file_path = os.path.join(root, file)
                path_info["files"].append({
                    "name": file,
                    "size": os.path.getsize(file_path)
                })
            for dir in dirs:
                path_info["dirs"].append(dir)
            result["contents"][rel_path] = path_info
    
    # Check for specific template
    template_id = request.args.get('template_id')
    if template_id:
        template_vis_dir = os.path.join(static_folder, "visualizations", template_id)
        result["template_vis_dir"] = {
            "path": template_vis_dir,
            "exists": os.path.exists(template_vis_dir),
            "files": []
        }
        if os.path.exists(template_vis_dir):
            for file in os.listdir(template_vis_dir):
                file_path = os.path.join(template_vis_dir, file)
                result["template_vis_dir"]["files"].append({
                    "name": file,
                    "size": os.path.getsize(file_path)
                })
    
    return jsonify(result)

# Add a test route for PDF generation
@app.route('/test_pdf_viz/<template_id>', methods=['GET'])
def test_pdf_visualization(template_id):
    """Test endpoint for generating PDF visualization."""
    try:
        # Get the template
        template = template_manager.get_template(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Find any PDF in uploads folder as a test
        pdf_path = None
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(UPLOAD_FOLDER, filename)
                break
        
        if not pdf_path:
            return jsonify({"error": "No PDF files found in uploads folder"}), 404
        
        # Generate visualization using the template fields and found PDF
        visualization_dir = os.path.join(PROCESSED_FOLDER, "visualizations", template_id)
        os.makedirs(visualization_dir, exist_ok=True)
        
        # Ensure static dir exists
        static_vis_dir = os.path.join(static_folder, "visualizations", template_id)
        os.makedirs(static_vis_dir, exist_ok=True)
        
        # Generate visualization
        logger.info(f"Test generating visualization for template {template_id} from {pdf_path}")
        visualization_data = visualize_extracted_fields(
            pdf_path=pdf_path,
            fields_data=template["fields"],
            output_dir=visualization_dir
        )
        
        # Copy files to static folder if needed
        for page_data in visualization_data.get("pages", []):
            page_num = page_data.get("page_number", 1)
            # Try both extensions
            for ext in ["png", "jpg"]:
                source_path = os.path.join(visualization_dir, f"page_{page_num}.{ext}")
                if os.path.exists(source_path):
                    dest_path = os.path.join(static_vis_dir, f"page_{page_num}.{ext}")
                    if not os.path.exists(dest_path):
                        logger.info(f"Copying {source_path} to {dest_path}")
                        import shutil
                        shutil.copy(source_path, dest_path)
        
        # Return visualization data
        return jsonify({
            "status": "success",
            "message": f"Generated visualization for template {template_id}",
            "visualization": visualization_data
        })
    
    except Exception as e:
        logger.error(f"Error in test PDF visualization: {str(e)}")
        return jsonify({"error": f"Error generating visualization: {str(e)}"}), 500

@app.route('/file_dump', methods=['GET'])
def file_dump():
    """Debug endpoint to dump information about all uploaded and visualization files."""
    result = {
        "upload_folder": UPLOAD_FOLDER,
        "upload_files": [],
        "processed_folder": PROCESSED_FOLDER,
        "visualization_folders": {},
        "static_folder": static_folder,
        "static_visualization_folders": {}
    }
    
    # List upload files
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                result["upload_files"].append({
                    "name": filename,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path),
                    "type": "pdf" if filename.lower().endswith(".pdf") else "other"
                })
    
    # List processed visualization folders
    visualization_dir = os.path.join(PROCESSED_FOLDER, "visualizations")
    if os.path.exists(visualization_dir):
        for folder in os.listdir(visualization_dir):
            folder_path = os.path.join(visualization_dir, folder)
            if os.path.isdir(folder_path):
                result["visualization_folders"][folder] = []
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        result["visualization_folders"][folder].append({
                            "name": filename, 
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path)
                        })
    
    # List static visualization folders
    static_vis_dir = os.path.join(static_folder, "visualizations")
    if os.path.exists(static_vis_dir):
        for folder in os.listdir(static_vis_dir):
            folder_path = os.path.join(static_vis_dir, folder)
            if os.path.isdir(folder_path):
                result["static_visualization_folders"][folder] = []
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        result["static_visualization_folders"][folder].append({
                            "name": filename, 
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path),
                            "url": f"/static/visualizations/{folder}/{filename}"
                        })
    
    # Check for a specific template
    template_id = request.args.get("template_id")
    if template_id:
        result["template_check"] = {
            "template_id": template_id,
            "processed_visualization_exists": False,
            "static_visualization_exists": False,
            "files": []
        }
        
        # Check processed folder
        template_vis_dir = os.path.join(PROCESSED_FOLDER, "visualizations", template_id)
        if os.path.exists(template_vis_dir):
            result["template_check"]["processed_visualization_exists"] = True
            for filename in os.listdir(template_vis_dir):
                file_path = os.path.join(template_vis_dir, filename)
                if os.path.isfile(file_path):
                    result["template_check"]["files"].append({
                        "location": "processed",
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path)
                    })
        
        # Check static folder
        static_template_vis_dir = os.path.join(static_folder, "visualizations", template_id)
        if os.path.exists(static_template_vis_dir):
            result["template_check"]["static_visualization_exists"] = True
            for filename in os.listdir(static_template_vis_dir):
                file_path = os.path.join(static_template_vis_dir, filename)
                if os.path.isfile(file_path):
                    result["template_check"]["files"].append({
                        "location": "static",
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path),
                        "url": f"/static/visualizations/{template_id}/{filename}"
                    })
        
        # Get the template data
        template = template_manager.get_template(template_id)
        if template:
            result["template_check"]["template_exists"] = True
            result["template_check"]["template_name"] = template.get("name")
            result["template_check"]["document"] = template.get("document")
            
            # Check if the document file exists
            document = template.get("document", {})
            original_filename = document.get("original_filename")
            stored_filename = document.get("stored_filename")
            file_id = document.get("file_id")
            
            if stored_filename and os.path.exists(os.path.join(UPLOAD_FOLDER, stored_filename)):
                result["template_check"]["document_file_exists"] = True
                result["template_check"]["document_file_path"] = os.path.join(UPLOAD_FOLDER, stored_filename)
            elif file_id:
                for filename in os.listdir(UPLOAD_FOLDER):
                    if filename.startswith(f"{file_id}_"):
                        result["template_check"]["document_file_exists"] = True
                        result["template_check"]["document_file_path"] = os.path.join(UPLOAD_FOLDER, filename)
                        break
            elif original_filename:
                for filename in os.listdir(UPLOAD_FOLDER):
                    if filename.endswith(original_filename):
                        result["template_check"]["document_file_exists"] = True
                        result["template_check"]["document_file_path"] = os.path.join(UPLOAD_FOLDER, filename)
                        break
        else:
            result["template_check"]["template_exists"] = False
    
    return jsonify(result)

@app.route('/force_visualization/<template_id>', methods=['GET'])
def force_visualization(template_id):
    """Force generation of visualization for a template, using all PDFs if needed."""
    try:
        # Get the template
        template = template_manager.get_template(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Try to find the PDF associated with this template
        pdf_path = None
        document = template.get("document", {})
        
        # First try using the stored filename
        stored_filename = document.get("stored_filename")
        if stored_filename:
            path = os.path.join(UPLOAD_FOLDER, stored_filename)
            if os.path.exists(path):
                pdf_path = path
        
        # Then try using the file ID
        if not pdf_path:
            file_id = document.get("file_id")
            if file_id:
                for filename in os.listdir(UPLOAD_FOLDER):
                    if filename.startswith(f"{file_id}_"):
                        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
                        break
        
        # Finally try using the original filename
        if not pdf_path:
            original_filename = document.get("original_filename")
            if original_filename:
                for filename in os.listdir(UPLOAD_FOLDER):
                    if filename.endswith(original_filename):
                        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
                        break
        
        # If we still can't find the PDF, try all PDFs in the upload folder
        if not pdf_path:
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
                    break
        
        if not pdf_path:
            return jsonify({"error": "No PDF files found in uploads folder"}), 404
            
        logger.info(f"Found PDF for template {template_id}: {pdf_path}")
        
        # Create visualization directories
        visualization_dir = os.path.join(PROCESSED_FOLDER, "visualizations", template_id)
        os.makedirs(visualization_dir, exist_ok=True)
        
        static_vis_dir = os.path.join(static_folder, "visualizations", template_id)
        os.makedirs(static_vis_dir, exist_ok=True)
        
        # Remove existing visualization files (force regeneration)
        for directory in [visualization_dir, static_vis_dir]:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed existing visualization file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {str(e)}")
        
        # Generate visualization
        logger.info(f"Generating visualization for template {template_id} from {pdf_path}")
        visualization_data = visualize_extracted_fields(
            pdf_path=pdf_path,
            fields_data=template["fields"],
            output_dir=visualization_dir
        )
        
        # Copy files to the static directory
        for page_data in visualization_data.get("pages", []):
            page_num = page_data.get("page_number", 1)
            
            for ext in ["png", "jpg"]:
                source_path = os.path.join(visualization_dir, f"page_{page_num}.{ext}")
                if os.path.exists(source_path):
                    dest_path = os.path.join(static_vis_dir, f"page_{page_num}.{ext}")
                    
                    try:
                        import shutil
                        shutil.copy2(source_path, dest_path)
                        logger.info(f"Copied visualization file from {source_path} to {dest_path}")
                    except Exception as e:
                        logger.error(f"Error copying file: {str(e)}")
        
        # Return visualization data with extra debug information
        return jsonify({
            "status": "success",
            "message": f"Force-generated visualization for template {template_id}",
            "pdf_path": pdf_path,
            "visualization_dir": visualization_dir,
            "static_vis_dir": static_vis_dir,
            "visualization": visualization_data,
            "pages": visualization_data.get("pages", [])
        })
    
    except Exception as e:
        logger.error(f"Error force-generating visualization: {str(e)}")
        return jsonify({
            "error": f"Error generating visualization: {str(e)}",
            "traceback": str(traceback.format_exc())
        }), 500

# Add a generic static file handler
@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    """Generic handler for all static files."""
    logger.debug(f"Generic static file request: {filename}")
    
    # Define potential locations in order of preference
    potential_paths = [
        app.static_folder,
        os.path.join(os.getcwd(), 'static'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
        os.path.join(os.path.dirname(__file__), 'static')
    ]
    
    # Try each path
    for base_path in potential_paths:
        file_path = os.path.join(base_path, filename)
        logger.debug(f"Trying static path: {file_path}")
        if os.path.exists(file_path) and os.path.isfile(file_path):
            logger.debug(f"Found static file at: {file_path}")
            return send_file(file_path)
    
    logger.warning(f"Static file not found: {filename}")
    return jsonify({"error": f"Static file {filename} not found"}), 404

# Add test route for debugging API routes
@app.route('/api/test_route', methods=['GET'])
def test_api_route():
    """Test route to verify API routing is working."""
    return jsonify({
        "status": "success",
        "message": "API test route is working properly",
        "static_folder": app.static_folder,
        "routes": [str(rule) for rule in app.url_map.iter_rules()]
    })

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the PDF Checkbox API')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind the server to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Run the Flask app
    app.run(host=args.host, port=args.port, debug=args.debug)
