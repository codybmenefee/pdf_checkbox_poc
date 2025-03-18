from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json
import os

def create_test_pdf(output_path, template_path):
    """Create a test PDF form based on the template JSON."""
    # Load the template
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    # Get PDF file path from template
    filename = template['document']['original_filename']
    output_file = os.path.join(output_path, filename)
    
    # Create the PDF
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, template['name'])
    
    # Add a description
    c.setFont("Helvetica", 10)
    c.drawString(72, height - 100, template['description'])
    
    # Add fields based on template
    c.setFont("Helvetica", 12)
    
    for field in template['fields']:
        # Convert normalized coordinates to absolute coordinates
        left = field['bbox']['left'] * width
        top = field['bbox']['top'] * height
        field_width = field['bbox']['width'] * width
        field_height = field['bbox']['height'] * height
        
        # Invert Y coordinate (PDF coordinates start from bottom)
        y_pos = height - top - field_height
        
        # Draw the field label
        c.drawString(left, y_pos - 15, field['label'])
        
        # Draw the field based on its type
        if field['field_type'] == 'checkbox':
            # Draw checkbox
            c.rect(left, y_pos, field_width, field_height, stroke=1, fill=0)
            
            # If the checkbox is checked, draw an X inside
            if field.get('default_value', False):
                c.line(left, y_pos, left + field_width, y_pos + field_height)
                c.line(left + field_width, y_pos, left, y_pos + field_height)
                
        elif field['field_type'] == 'text':
            # Draw text field
            c.rect(left, y_pos, field_width, field_height, stroke=1, fill=0)
            
            # Add default value if any
            if field.get('default_value'):
                c.setFont("Helvetica", 10)
                c.drawString(left + 2, y_pos + 2, str(field['default_value']))
                c.setFont("Helvetica", 12)
                
        elif field['field_type'] == 'date':
            # Draw date field
            c.rect(left, y_pos, field_width, field_height, stroke=1, fill=0)
            
            # Add default value if any
            if field.get('default_value'):
                c.setFont("Helvetica", 10)
                c.drawString(left + 2, y_pos + 2, str(field['default_value']))
                c.setFont("Helvetica", 12)
                
        elif field['field_type'] == 'signature':
            # Draw signature box
            c.rect(left, y_pos, field_width, field_height, stroke=1, fill=0)
            c.setFont("Helvetica", 8)
            c.drawString(left + 2, y_pos + 2, "Signature")
            c.setFont("Helvetica", 12)
    
    # Add information footer
    c.setFont("Helvetica", 8)
    c.drawString(72, 30, f"Template ID: {template['template_id']} | Version: {template['version']}")
    c.drawString(72, 20, f"Generated for PDF field visualization testing")
    
    # Save the PDF
    c.save()
    print(f"Test PDF created: {output_file}")
    return output_file

def main():
    # Create output directory
    output_dir = "data/test_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate PDF based on template
    template_path = "data/templates/test_visualization_template.json"
    create_test_pdf(output_dir, template_path)
    
    print("Test PDF generation completed.")

if __name__ == "__main__":
    main() 