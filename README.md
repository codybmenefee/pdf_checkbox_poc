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
   ./run.sh
   ```

## Testing

Run tests using:
```
python src/run_tests.py
```

For visualization-specific tests:
```
python src/run_visualization_tests.py
```

## License

[MIT License](LICENSE)
