# PDF Field Visualization Test Suite

This is a simplified test suite for visualizing form fields on PDF documents. It provides a lightweight way to rapidly iterate on field visualization features without requiring the full application stack.

## Overview

The test suite consists of:

1. A test form generator (`create_test_form.py`) that creates a simple PDF with various form fields
2. A PDF page extractor (`extract_pdf_page.py`) that converts PDF pages to images for browser display
3. A standalone HTML visualization tool (`standalone_field_test.html`) that displays fields on top of the PDF image
4. A runner script (`run_field_test.py`) that ties everything together

## Requirements

- Python 3.7+
- Required Python packages (install via pip):
  - reportlab (for PDF generation)
  - pdf2image (for PDF-to-image conversion)
  - pillow (for image processing)
- Poppler (required by pdf2image for PDF rendering):
  - On macOS: `brew install poppler`
  - On Ubuntu/Debian: `apt-get install poppler-utils`
  - On Windows: Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)

## Getting Started

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the test suite:
   ```bash
   python src/run_field_test.py
   ```

3. The script will:
   - Generate a test form PDF if it doesn't exist
   - Convert the PDF to images
   - Start a local HTTP server
   - Open a browser with the visualization tool

4. In the visualization tool, you can:
   - Upload the generated PDF image
   - Edit the field data in the JSON textarea
   - Render fields on top of the PDF
   - Adjust field sizes and toggle labels

## File Descriptions

- `src/create_test_form.py`: Generates a test PDF with form fields
- `src/extract_pdf_page.py`: Extracts pages from a PDF as images
- `src/standalone_field_test.html`: Browser-based visualization tool
- `src/run_field_test.py`: Runner script that executes the workflow
- `src/data/test_form_template.json`: Field definitions matching the test form
- `src/data/test_form_with_fields.pdf`: Generated test form

## Custom Field Data

You can modify the field data in the JSON textarea to test different field types, positions, and sizes. Each field should have:

- `id`: Unique identifier
- `name`: Display name
- `type`: Field type (checkbox, text, signature, date, etc.)
- `page`: Page number
- `bbox`: Bounding box with normalized coordinates (left, top, width, height)
- `value`: Field value (true/false for checkboxes, text for other fields)

Example field:
```json
{
  "id": "new_client",
  "name": "New Client",
  "type": "checkbox",
  "page": 1,
  "bbox": {
    "left": 0.125,
    "top": 0.25,
    "width": 0.015,
    "height": 0.015
  },
  "value": true
}
```

## Using Your Own PDFs

To use your own PDFs:

1. Convert your PDF to images using the `extract_pdf_page.py` script:
   ```bash
   python src/extract_pdf_page.py your_pdf.pdf -o output_directory -d 150
   ```

2. Create a JSON file with field definitions for your PDF, using normalized coordinates (0-1 range)

3. Run the standalone HTML tool and:
   - Upload your PDF image
   - Paste your field definitions
   - Click "Render Fields"

## Troubleshooting

- **PDF to image conversion fails**: Make sure Poppler is installed correctly
- **Fields not showing in the right position**: Verify the coordinates in the field data
- **Image upload not working**: Try a different image format (PNG works best)

## Next Steps

After testing and refining the field visualization in the standalone tool, you can apply the changes to the main application by:

1. Updating the CSS classes in the main application's stylesheets
2. Modifying the JavaScript rendering functions in `field-visualization.js`
3. Ensuring the data format in the API matches what's expected by the visualization components 