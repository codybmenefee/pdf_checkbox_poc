# PDF Checkbox POC

A proof of concept application for automated PDF form checkbox detection and filling using Google Document AI.

## Repository

This project is available on GitHub:
- Repository URL: https://github.com/codybmenefee/pdf_checkbox_poc
- Clone with: `git clone https://github.com/codybmenefee/pdf_checkbox_poc.git`

## Overview

This project allows users to:
- Upload PDF forms
- Automatically detect checkboxes and form fields
- Create templates for form filling
- Fill forms with data
- Visualize form fields and checkboxes

## Architecture

### Database Structure

MongoDB is used for data storage with modular components:

- `db_core.py` - Connection management and base operations
- `db_models.py` - Data models and schema definitions
- `db_queries.py` - Query builders and complex operations
- `db_utils.py` - Helper functions and utilities
- `database.py` - Compatibility layer that re-exports these components

### Core Components

- **Document AI Integration**: Uses Google Document AI for document processing (`document_ai_client.py`)
- **PDF Handling**: PDF upload, processing, and storage (`pdf_handler.py`)
- **Form Filling**: Automated form filling based on templates (`form_filler.py`)
- **Template Management**: Template creation and management (`template_manager.py`)
- **Visualization**: Visualization of form fields and checkboxes (`visualization.py`)
- **API Layer**: REST API for client interactions (`ui_api.py`, `form_api.py`, `db_api.py`)

### Static File Management

The application serves static files (including visualizations and UI assets) through multiple endpoints:

- `/static/*` - Standard static file access
- `/api/visualizations/<id>/*` - API access to visualization files
- `/api/ui_visualizations/<id>/*` - Alternative API access to visualization files

See the [Static File Configuration](docs/static_file_configuration.md) documentation for more details.

### Field Visualization

The application provides comprehensive visualization capabilities for form fields, allowing users to:
- View field positions on PDF pages
- Highlight detected checkboxes
- See field properties and relationships

For detailed information, see the [Field Visualization](docs/field_visualization.md) documentation.

### Web Interface

Flask-based web application with routes defined in `app.py`.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables by copying `.env.template` to `.env` and filling in the required values
4. Set up a MongoDB database
5. Set up a Google Cloud project with Document AI enabled
6. Run the application:
   ```
   ./scripts/run.sh
   ```

## Testing

Run all tests using:
```
python tests/run_all_tests.py
```

For specific test categories:
```
python tests/run_tests.py            # Core functionality tests
python tests/run_visualization_tests.py  # Visualization tests
```

For static file handling tests:
```
python -m unittest src/test_static_file_handling.py
```

## Utility Tools

The `tools/` directory contains utility scripts for development and testing:

- `generate_test_pdf.py` - Generates test PDF files based on templates
- `generate_placeholders.py` - Generates placeholder elements for testing
- `debug_template_check.py` - Validates templates for potential issues

The `scripts/` directory contains shell scripts for various operations:

- `run.sh` - Main script to run the application
- `run_field_test.sh` - Script to run field detection tests
- `setup_visualization.sh` - Sets up the visualization environment

## Project Organization

- `src/` - Source code for the application
- `tools/` - Python utility scripts for development and testing
- `scripts/` - Shell scripts for running the application and tests
- `docs/` - Project documentation and references
- `tests/` - Test suite and test cases
- `data/` - Data files and sample PDFs
- `logs/` - Log files produced by the application
- `.github/` - GitHub-specific files like PR templates

## Documentation

- [API Documentation](docs/api_documentation.md)
- [Architecture Design](docs/architecture_design.md)
- [Field Visualization](docs/field_visualization.md)
- [Static File Configuration](docs/static_file_configuration.md)
- [Technical Documentation](docs/technical_documentation.md)
- [User Guide](docs/user_guide.md)

## License

[MIT License](LICENSE)
