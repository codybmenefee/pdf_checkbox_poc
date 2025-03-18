"""
Generate test document page images for field visualization.
"""

import os
import json
import logging
from src.visualization import generate_test_document_pages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Generate test document page images for the sample document.
    """
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(base_dir, 'src', 'data', 'processed', 'visualizations', 'test_fields')
    output_dir = os.path.join(base_dir, 'src', 'static', 'visualizations', 'test_fields')
    pdf_path = os.path.join(test_dir, 'NCAF - Secured.Entity - English.pdf')
    
    # Ensure the test document exists
    if not os.path.exists(pdf_path):
        logger.error(f"Test PDF not found: {pdf_path}")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Generate page images
        pages = generate_test_document_pages(pdf_path, output_dir)
        
        # Load existing field data
        data_file = os.path.join(test_dir, 'field_visualization_data.json')
        with open(data_file, 'r') as f:
            field_data = json.load(f)
        
        # Update page data
        field_data['pages'] = pages
        
        # Save updated data to visualization output directory
        output_data_file = os.path.join(output_dir, 'field_data.json')
        with open(output_data_file, 'w') as f:
            json.dump(field_data, f, indent=2)
        
        logger.info(f"Generated {len(pages)} page images")
        logger.info(f"Updated field data saved to {output_data_file}")
        logger.info(f"Access the visualization at: http://localhost:5000/ui/field-visualization/test_fields")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating test pages: {str(e)}")
        return False

if __name__ == "__main__":
    main() 