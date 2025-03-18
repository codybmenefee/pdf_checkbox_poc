# Google Document AI Form Parser Research Findings

## Overview
This document summarizes the research findings on Google Document AI's Form Parser API for the Automated Checkbox Extraction & Form Filling System POC. The research focused on understanding the capabilities of the Form Parser API for detecting checkboxes, determining their states, and extracting their coordinates.

## Form Parser Capabilities

### Checkbox Detection
- Form Parser includes a high-quality selection mark detector that can extract checkboxes from both images and PDFs
- Checkboxes are output as key-value pairs (KVPs), using the text nearest to the checkbox as the key
- The `valueType` field indicates whether a checkbox is filled or unfilled
- The system can reliably detect the state of checkboxes (checked vs. unchecked)

### Bounding Box Coordinates
- Form Parser provides bounding box coordinates for all detected elements, including checkboxes
- Coordinates are provided in the `boundingPoly` field of the layout object
- The top-left corner of the page is the origin (0,0), with positive X values to the right and positive Y values down
- Coordinates are provided in two formats:
  - `vertices`: Uses the same coordinates as the original image
  - `normalizedVertices`: Coordinates in the range [0,1] for scaling purposes
- When a coordinate value is 0, that coordinate may be omitted in the JSON response

### Document Object Structure
- The response to a processing request contains a `Document` object with all extracted information
- The `text` field contains the raw text recognized in the document
- Each page in the document corresponds to a physical page from the sample document
- Elements have a corresponding `layout` that describes their position and text
- The `textAnchor` object references the main text string with `startIndex` and `endIndex`

### API Authentication and Setup
- Requires a Google Cloud project with the Document AI API enabled
- Authentication is handled through Google Cloud credentials
- A Form Parser processor must be created in the Google Cloud Console
- The processor ID, project ID, and location are required for API calls

## Implementation Considerations

### Required Libraries
- `google-cloud-documentai`: Main library for interacting with the Document AI API
- Image processing libraries (e.g., `wand`, `PIL`) for visualization of bounding boxes
- PDF processing libraries (e.g., `PyPDF2`) for handling PDF documents

### Processing Flow
1. Set up authentication and create a Document AI client
2. Prepare the document for processing (read file into memory)
3. Send the document to the Form Parser processor
4. Process the response to extract checkbox information
5. Store the extracted data (checkbox coordinates, states, and associated text)

### Limitations
- The checkbox model doesn't support parsing radio buttons
- Some detected checkboxes might not have corresponding keys
- The model doesn't reliably parse a KVP with an unfilled value (blank form)
- KVP parsing on documents in certain languages may have lower quality than Latin languages

## Example Code Snippets

### Authentication and Client Setup
```python
from google.cloud import documentai_v1beta3 as documentai

# Set up variables
PROJECT_ID = "YOUR_PROJECT_ID"
LOCATION = "us"  # Format is 'us' or 'eu'
PROCESSOR_ID = "PROCESSOR_ID"  # Create processor in Cloud Console

# Initialize client
client = documentai.DocumentProcessorServiceClient()

# The full resource name of the processor
name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
```

### Processing a Document
```python
# Read the file into memory
with open("form.pdf", "rb") as image:
    image_content = image.read()

# Configure the process request
document = {"content": image_content, "mime_type": "application/pdf"}
request = {"name": name, "document": document}

# Process the document
result = client.process_document(request=request)
document = result.document
```

### Extracting Checkbox Information
```python
# Extract form fields
for page in document.pages:
    for form_field in page.form_fields:
        field_name = get_text(form_field.field_name, document)
        field_value = get_text(form_field.field_value, document)
        
        # Check if this is a checkbox (valueType indicates checkbox state)
        if hasattr(form_field.field_value, 'value_type'):
            is_checked = form_field.field_value.value_type == 'selected'
            
        # Get bounding box coordinates
        if form_field.field_value.layout:
            bounding_poly = form_field.field_value.layout.bounding_poly
            vertices = bounding_poly.vertices
            # Process coordinates for storage
```

## Conclusion
Google Document AI's Form Parser API provides robust capabilities for checkbox detection and extraction, making it suitable for the Automated Checkbox Extraction & Form Filling System POC. The API can reliably detect checkboxes, determine their states, and provide precise coordinates, which can be used to create templates for form filling.

## References
1. [Google Cloud Document AI Form Parser Documentation](https://cloud.google.com/document-ai/docs/form-parser)
2. [Handle Processing Response Documentation](https://cloud.google.com/document-ai/docs/handle-response)
3. [GitHub Example: documentai-bounding-boxes](https://github.com/asrivas/documentai-bounding-boxes)
