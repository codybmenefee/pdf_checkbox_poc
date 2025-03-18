# PDF Field Visualization Feature

This document provides information on how to use the PDF field visualization feature, which allows users to view and edit field positions on PDF templates.

## Overview

The PDF field visualization feature provides an interactive interface to:

1. Visualize form fields overlaid on PDF documents
2. Adjust field positions and sizes directly on the document
3. Filter fields by type
4. Export template data as JSON
5. Save changes to field positions

## Accessing the Visualization

There are two ways to access the field visualization:

1. **From the Templates Page**: 
   - Navigate to the Templates page
   - Find the template you want to visualize
   - Click on the "Enhanced View" button

2. **Direct URL**: 
   - Access directly via `/ui/template-advanced-visualization/{template_id}`

## Using the Visualization Interface

### Interface Components

The visualization interface consists of:

1. **Document Viewer**: Shows the PDF with field overlays
2. **Controls Panel**: 
   - Display options
   - Field size adjustment
   - Field type filtering
   - Debug mode
3. **Field List**: Shows all fields on the current page
4. **Page Navigation**: Navigate between document pages

### Field Display

Fields are color-coded by type:
- **Text Fields**: Green
- **Checkbox Fields**: Blue
- **Signature Fields**: Red
- **Date Fields**: Yellow

### Interacting with Fields

- **Move Fields**: Drag and drop a field to change its position
- **Resize Fields**: Click and drag field edges or corners
- **Toggle Visibility**:
  - Use the "Show Field Overlays" toggle in the Controls Panel
  - Filter by field type using the checkboxes

### Saving Changes

1. Adjust fields as needed
2. Click the "Save Changes" button in the Controls Panel
3. Changes will be saved to the template with an incremented version number
4. A backup of the original template is automatically created

### Exporting Data

1. Click the "Export JSON" button
2. The template data will be downloaded as a JSON file

## Testing with Sample Documents

For testing purposes, you can use the provided test PDF files:

1. Navigate to `data/test_pdfs/` to find the test PDF documents
2. These documents match the layout defined in `data/templates/test_visualization_template.json`

## Best Practices

1. **Always save changes** after making significant adjustments
2. Use **Debug Mode** to see coordinates when precise positioning is needed
3. **Export a backup** of your template data before making major changes
4. For large templates, use the **field type filters** to focus on specific fields

## Troubleshooting

### Common Issues

1. **PDF not loading**:
   - Check that the PDF file exists in the correct location
   - Verify file permissions

2. **Fields not appearing**:
   - Check that fields are defined in the template
   - Verify that fields have valid coordinates (bbox values)

3. **Changes not saving**:
   - Ensure the template directory is writable
   - Check application logs for errors

### Error Messages

- **PDF_NOT_FOUND**: The PDF file specified in the template could not be found
- **PDF_CONVERSION_FAILED**: The PDF file could not be converted to images
- **VISUALIZATION_FAILED**: General error in creating the visualization

## Advanced Features

### Performance Optimization

For large templates with many fields, you can improve performance by:

1. Using field type filters
2. Adjusting the field size multiplier to make fields easier to see/select
3. Using debug mode to see exact coordinates for precise adjustments

### Custom Field Types

The system supports adding new field types. To add a new field type:

1. Update the CSS classes in the template_advanced_visualization.html file
2. Add the new type to the field type filter list
3. Update the backend to handle the new field type

## Reference

### Field Object Structure

```json
{
  "field_id": "unique-id",
  "name": "Field Name",
  "label": "Field Label",
  "field_type": "text|checkbox|signature|date",
  "page": 1,
  "default_value": "",
  "bbox": {
    "left": 0.15,
    "top": 0.25,
    "width": 0.4,
    "height": 0.03
  }
}
```

### Key Files

- `src/templates/template_advanced_visualization.html`: Main visualization UI
- `src/visualization.py`: Backend visualization functions
- `src/ui_api.py`: API endpoints for the visualization feature
- `data/templates/test_visualization_template.json`: Sample template 