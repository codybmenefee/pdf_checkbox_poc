# Static File Configuration

This document explains how static files are configured and served in the PDF Checkbox POC application.

## Overview

Static files in the application include:
- PDF page visualizations
- Checkbox and field overlays
- Placeholder and error images
- UI assets

## File Structure

The application uses the following directory structure for static files:

```
pdf_checkbox_poc/
├── static/                          # Primary static files directory
│   ├── images/                      # General images
│   │   ├── loading-placeholder.png  # Loading placeholder
│   │   └── error-placeholder.png    # Error placeholder
│   ├── visualizations/              # Visualization files
│   │   ├── [visualization-id]/      # Directory per visualization
│   │   │   ├── page_1.png           # Page renderings
│   │   │   ├── page_2.png
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```

## Configuration

The Flask application is configured to serve static files from multiple locations:

1. **Primary static folder**: Set explicitly in the app configuration:
   ```python
   app.static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
   app.static_url_path = '/static'
   ```

2. **Multiple search paths**: Static files are searched for in multiple locations to provide flexibility:
   - Application static folder (`app.static_folder`)
   - Project root static folder (`os.path.join(os.getcwd(), 'static')`)
   - Processed files folder (`PROCESSED_FOLDER`)
   - Upload folder (`UPLOAD_FOLDER`)

## Endpoints

The application provides multiple endpoints for accessing static files:

1. **Standard static endpoint**: `/static/<path:filename>`
   - Serves files from the static folder

2. **Visualization-specific endpoint**: `/static/visualizations/<visualization_id>/<path:filename>`
   - Serves visualization files with additional fallback locations

3. **API visualization endpoint**: `/api/visualizations/<visualization_id>/<path:filename>`
   - Serves visualization files through the API

## Debugging

For troubleshooting static file issues, the application provides a debug endpoint:

- `/static_debug` - Returns JSON information about the static folder configuration and contents

## Adding New Static Files

When adding new static files:

1. Place them in the appropriate subdirectory of the static folder
2. Access them using the standard URL pattern: `/static/path/to/file.ext`

For visualization files:

1. Generated files should be saved to both the processed folder and static folder
2. Use the visualization ID as a subdirectory to organize files

## Common Issues

If static files are not loading:

1. Verify the file exists in the expected location
2. Check Flask logs for file path resolution issues
3. Ensure the static folder is properly configured
4. Use the `/static_debug` endpoint to inspect the static folder configuration 