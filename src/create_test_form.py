"""
Create a simple PDF test form with checkbox fields
for testing the visualization feature.
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_test_form(output_path):
    """
    Create a simple test form with various field types.
    
    Args:
        output_path: Path to save the PDF
    """
    # Create the directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create the canvas
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Test Form for Field Visualization")
    
    # Add a section header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, height - 2*inch, "Client Information")
    
    # Draw a line
    c.setStrokeColor(colors.black)
    c.line(1*inch, height - 2.2*inch, width - 1*inch, height - 2.2*inch)
    
    # Add checkboxes with labels
    c.setFont("Helvetica", 10)
    
    # Checkbox 1
    c.rect(1*inch, height - 2.5*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(1.2*inch, height - 2.5*inch, "New Client")
    
    # Checkbox 2
    c.rect(3*inch, height - 2.5*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(3.2*inch, height - 2.5*inch, "Existing Client")
    
    # Checkbox 3
    c.rect(5*inch, height - 2.5*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(5.2*inch, height - 2.5*inch, "VIP Client")
    
    # Add form fields with labels
    c.setFont("Helvetica-Bold", 10)
    
    # Name field
    c.drawString(1*inch, height - 3*inch, "Name:")
    c.line(2*inch, height - 3*inch, 7*inch, height - 3*inch)
    
    # Email field
    c.drawString(1*inch, height - 3.5*inch, "Email:")
    c.line(2*inch, height - 3.5*inch, 7*inch, height - 3.5*inch)
    
    # Phone field
    c.drawString(1*inch, height - 4*inch, "Phone:")
    c.line(2*inch, height - 4*inch, 4*inch, height - 4*inch)
    
    # Date field
    c.drawString(5*inch, height - 4*inch, "Date:")
    c.line(6*inch, height - 4*inch, 7*inch, height - 4*inch)
    
    # Add another section header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, height - 5*inch, "Service Selection")
    
    # Draw a line
    c.line(1*inch, height - 5.2*inch, width - 1*inch, height - 5.2*inch)
    
    # Add more checkboxes
    c.setFont("Helvetica", 10)
    
    # Service 1
    c.rect(1*inch, height - 5.5*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(1.2*inch, height - 5.5*inch, "Basic Plan")
    
    # Service 2
    c.rect(3*inch, height - 5.5*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(3.2*inch, height - 5.5*inch, "Standard Plan")
    
    # Service 3
    c.rect(5*inch, height - 5.5*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(5.2*inch, height - 5.5*inch, "Premium Plan")
    
    # Add options with checkboxes
    # Option 1
    c.rect(1*inch, height - 6*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(1.2*inch, height - 6*inch, "Auto-renewal")
    
    # Option 2
    c.rect(3*inch, height - 6*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(3.2*inch, height - 6*inch, "Send promotions")
    
    # Option 3
    c.rect(5*inch, height - 6*inch, 0.12*inch, 0.12*inch, stroke=1, fill=0)
    c.drawString(5.2*inch, height - 6*inch, "Newsletter subscription")
    
    # Add signature box
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, height - 7*inch, "Signature:")
    c.rect(2*inch, height - 7.5*inch, 3*inch, 0.7*inch, stroke=1, fill=0)
    
    # Add date box
    c.drawString(5.5*inch, height - 7*inch, "Date:")
    c.rect(6*inch, height - 7.1*inch, 1*inch, 0.25*inch, stroke=1, fill=0)
    
    # Add form ID at the bottom
    c.setFont("Helvetica", 8)
    c.drawString(width - 2*inch, 0.5*inch, "Form ID: TEST-FORM-123")
    
    # Save the PDF
    c.save()
    
    print(f"Test form created at: {output_path}")

if __name__ == "__main__":
    output_path = os.path.join("src", "data", "test_form_with_fields.pdf")
    create_test_form(output_path) 