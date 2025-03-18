"""
Simple test script to visualize form fields on a PDF.
This is a focused, simplified version of the field visualization feature
for rapid iteration and debugging.
"""

import os
import json
from flask import Flask, render_template, jsonify, send_from_directory
import tempfile
import shutil
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO

# Create a Flask app for testing
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Sample field data - customize this with your actual field data
SAMPLE_FIELDS = [
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
        "name": "Add Account",
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
        "id": "signature",
        "name": "Signature",
        "type": "signature",
        "page": 1,
        "bbox": {
            "left": 0.4,
            "top": 0.7,
            "width": 0.2,
            "height": 0.05
        },
        "value": ""
    },
    {
        "id": "date",
        "name": "Date",
        "type": "date",
        "page": 1,
        "bbox": {
            "left": 0.7,
            "top": 0.7,
            "width": 0.1,
            "height": 0.05
        },
        "value": ""
    }
]

# Path to PDF, using the provided PDF in the codebase
PDF_PATH = "src/test_form.pdf"
TEST_DOCUMENT_ID = "test_doc_123"

# Temporary directory for storing images
temp_dir = None

@app.route('/')
def index():
    """Display the field visualization page."""
    return render_template('field_visualization.html', document_id=TEST_DOCUMENT_ID)

@app.route('/ui/field-visualization/<document_id>')
def field_visualization_ui(document_id):
    """Serve the field visualization template."""
    return render_template('field_visualization.html', document_id=document_id)

@app.route('/api/field-visualization/<document_id>')
def get_field_visualization_data(document_id):
    """API endpoint to get field extraction visualization data."""
    global temp_dir
    
    # Create a temporary directory for page images
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    # Convert PDF pages to images
    try:
        pages = convert_from_path(PDF_PATH)
        page_data = []
        
        for i, page_image in enumerate(pages):
            # Save the page image
            page_number = i + 1
            image_path = os.path.join(temp_dir, f"page_{page_number}.png")
            page_image.save(image_path)
            
            # Create page data
            page_data.append({
                "page_number": page_number,
                "image_url": f"/test/pages/page_{page_number}.png",
                "width": page_image.width,
                "height": page_image.height
            })
        
        # Count fields by type
        field_types = {}
        for field in SAMPLE_FIELDS:
            field_type = field.get("type", "other")
            field_types[field_type] = field_types.get(field_type, 0) + 1
        
        # Return full visualization data
        return jsonify({
            "document_id": document_id,
            "document_name": "Test Form",
            "processing_date": "2023-11-30T12:00:00Z",
            "total_pages": len(pages),
            "pages": page_data,
            "fields": SAMPLE_FIELDS,
            "field_types": field_types
        })
    
    except Exception as e:
        print(f"Error generating visualization data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test/pages/<filename>')
def serve_page_image(filename):
    """Serve the page images from the temporary directory."""
    global temp_dir
    if temp_dir:
        return send_from_directory(temp_dir, filename)
    return "Page not found", 404

@app.route('/ui/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

def cleanup():
    """Remove temporary directory and files."""
    global temp_dir
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        temp_dir = None

if __name__ == '__main__':
    try:
        print("Starting test server at http://localhost:5005/")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, port=5005)
    finally:
        cleanup() 