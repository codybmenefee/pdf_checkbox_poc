# PDF Checkbox Extraction & Form Filling System - User Guide

## Introduction

The PDF Checkbox Extraction & Form Filling System is a powerful tool designed to automate the extraction of checkbox fields from PDF documents and enable efficient form filling. This guide will walk you through the system's features and how to use them effectively.

## Getting Started

### Installation

This project is available on GitHub:
- Repository URL: https://github.com/codybmenefee/pdf_checkbox_poc
- Clone with: `git clone https://github.com/codybmenefee/pdf_checkbox_poc.git`

To install and run the application:
1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Copy `.env.template` to `.env` and configure your environment variables
4. Run the application with `./run.sh`

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, or Edge)
- Internet connection
- Google Cloud account with Document AI API enabled
- API key for authentication

### Accessing the System

1. Navigate to the system URL in your web browser
2. Log in using your credentials
3. You'll be directed to the dashboard

## Key Features

### 1. PDF Checkbox Extraction

The system uses Google Document AI's Form Parser API to automatically detect checkboxes in PDF documents. It can:

- Identify both checked and unchecked boxes
- Extract precise coordinates for each checkbox
- Determine the text labels associated with checkboxes
- Process multi-page documents

### 2. Template Management

Templates store the extracted checkbox field data for reuse:

- Create templates from processed PDF documents
- Tag templates for easy organization
- Version control for template updates
- Search and filter capabilities

### 3. Form Filling

Apply templates to fill forms automatically:

- Map templates to new PDF documents
- Fill checkboxes based on field values
- Handle different PDF dimensions with proper scaling
- Preview filled forms before finalizing

### 4. Validation and Correction

Ensure accuracy with validation tools:

- Visual validation interface
- Position adjustment for fields
- Value correction capabilities
- Audit logging for changes

### 5. Export Options

Export filled forms to various destinations:

- OneSpan integration for e-signatures
- DocuSign integration for e-signatures
- Direct PDF download
- Export history tracking

## Workflow Guide

### Step 1: Upload and Process a PDF

1. From the dashboard, click on "Templates" in the navigation menu
2. Click the "Create New Template" button
3. Upload a PDF document containing checkboxes
4. The system will process the document using Google Document AI
5. Review the extracted checkboxes

### Step 2: Create a Template

1. After processing, provide a name and description for your template
2. Add tags if desired for organization
3. Review the extracted fields and make any necessary adjustments
4. Click "Save Template"

### Step 3: Fill a Form

1. Navigate to the "Forms" section
2. Click "Create New Form"
3. Select a template from the dropdown
4. Upload the PDF document you want to fill
5. Set the values for each checkbox field
6. Click "Fill Form"

### Step 4: Validate and Correct

1. From the Forms list, find your filled form
2. Click "Validate" to open the validation interface
3. Review the checkbox placements on the PDF
4. Make corrections if needed by adjusting positions or values
5. Save your corrections

### Step 5: Export the Form

1. From the Forms list, find your validated form
2. Click "Export" to open the export interface
3. Select your desired export destination (OneSpan, DocuSign, or Download)
4. Configure any export-specific settings
5. Click "Export" to complete the process

## Template Management

### Creating Templates

1. Navigate to the Templates section
2. Click "Create New Template"
3. Upload a PDF document
4. Review extracted checkboxes
5. Provide template details and save

### Managing Templates

- **Search**: Use the search bar to find templates by name
- **Filter**: Filter templates by tags
- **View Details**: Click on a template to view its details
- **Edit**: Update template information or field data
- **Delete**: Remove templates you no longer need
- **Version Control**: Create new versions of existing templates

## Form Management

### Creating Forms

1. Navigate to the Forms section
2. Click "Create New Form"
3. Select a template
4. Upload a PDF to fill
5. Configure field values
6. Fill the form

### Managing Forms

- **Search**: Find forms by name
- **Filter**: Filter by template or status
- **View Details**: See form information and field values
- **Download**: Get the filled PDF
- **Validate**: Check and correct field placements
- **Export**: Send to e-signature platforms

## Validation Tools

### Visual Validation

1. Open a form for validation
2. The system displays the PDF with checkbox overlays
3. Red overlays indicate potential issues
4. Green overlays indicate validated fields

### Making Corrections

1. Select a field from the validation panel
2. Use the correction panel to adjust:
   - Field value (checked/unchecked)
   - Position (X/Y coordinates)
3. Apply the correction
4. Save all corrections when finished

## Export Options

### OneSpan Export

1. Select OneSpan as the export destination
2. Enter signer information:
   - Email address
   - Name
   - Expiry period
3. Choose whether to send email notification
4. Complete the export

### DocuSign Export

1. Select DocuSign as the export destination
2. Enter recipient information:
   - Email address
   - Name
   - Email subject and message
3. Complete the export

### Direct Download

1. Select Download as the export option
2. Choose whether to flatten the PDF
3. Download the filled form

## Troubleshooting

### Common Issues

1. **PDF Processing Fails**
   - Ensure the PDF is not password-protected
   - Check that the file size is under 10MB
   - Verify that the PDF contains actual checkboxes (not images of checkboxes)

2. **Checkbox Detection Issues**
   - Some checkbox styles may not be recognized
   - Try adjusting the document quality or scanning settings
   - Manual field addition is available for undetected checkboxes

3. **Form Filling Problems**
   - Verify template and target document compatibility
   - Check for significant layout differences between documents
   - Use the validation tools to correct field placements

### Getting Help

For additional assistance:
- Check the API documentation for integration help
- Contact system administrators for account issues
- Submit bug reports through the feedback form

## Best Practices

1. **Template Organization**
   - Use consistent naming conventions
   - Apply tags for categorization
   - Document template purposes and usage

2. **Form Processing**
   - Test templates with sample documents before production use
   - Validate all filled forms before export
   - Keep original PDFs for reference

3. **System Integration**
   - Use the API for batch processing
   - Set up webhooks for automated workflows
   - Implement proper error handling in integrations

## Conclusion

The PDF Checkbox Extraction & Form Filling System streamlines the process of working with checkbox-based PDF forms. By leveraging Google Document AI technology and providing robust template management, form filling, validation, and export capabilities, the system significantly reduces the manual effort required for form processing.

For technical details and API integration, please refer to the API Documentation.
