"""
Run the complete field visualization test workflow.

This script:
1. Generates a test form PDF
2. Converts the PDF to images
3. Opens the standalone visualization HTML in a browser
"""

import os
import sys
import json
import webbrowser
import http.server
import socketserver
import threading
import time

# Import our test scripts
from create_test_form import create_test_form
from extract_pdf_page import extract_pdf_pages

# Define paths
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "src", "data")
PDF_PATH = os.path.join(DATA_DIR, "test_form_with_fields.pdf")
TEMPLATE_PATH = os.path.join(DATA_DIR, "test_form_template.json")
HTML_PATH = os.path.join(PROJECT_DIR, "src", "standalone_field_test.html")

def ensure_directory(path):
    """Ensure directory exists"""
    if not os.path.exists(path):
        os.makedirs(path)

def run_http_server():
    """Run a simple HTTP server to serve the HTML file"""
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    os.chdir(PROJECT_DIR)  # Change to project directory
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}/")
        print(f"View the test page at http://localhost:{PORT}/src/standalone_field_test.html")
        httpd.serve_forever()

def main():
    """Run the complete test workflow"""
    print("Starting field visualization test workflow")
    
    # Ensure data directory exists
    ensure_directory(DATA_DIR)
    
    # Step 1: Generate test form if it doesn't exist
    if not os.path.exists(PDF_PATH):
        print("Generating test form PDF...")
        create_test_form(PDF_PATH)
    else:
        print(f"Using existing test form: {PDF_PATH}")
    
    # Step 2: Extract PDF to image(s)
    print("Converting PDF to images...")
    output_paths = extract_pdf_pages(PDF_PATH, DATA_DIR, dpi=150)
    if not output_paths:
        print("Error: Failed to extract PDF pages")
        sys.exit(1)
    
    # Print information for use in the HTML test tool
    print("\nTest Setup Complete!")
    print("=====================")
    print(f"1. Test form PDF: {PDF_PATH}")
    print(f"2. Page images:")
    for path in output_paths:
        print(f"   - {path}")
    
    # Step 3: Load field template data
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, 'r') as f:
            template_data = json.load(f)
        
        print(f"3. Field definitions loaded from: {TEMPLATE_PATH}")
        print(f"   - {len(template_data['fields'])} fields defined")
    else:
        print(f"Warning: Template file not found: {TEMPLATE_PATH}")
    
    # Step 4: Start HTTP server and open browser
    print("\nStarting HTTP server...")
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(1)
    
    # Open browser with the test page
    test_url = f"http://localhost:8000/src/standalone_field_test.html"
    print(f"Opening browser to: {test_url}")
    webbrowser.open(test_url)
    
    print("\nTest server is running. Press Ctrl+C to exit.")
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest server stopped.")

if __name__ == "__main__":
    main() 