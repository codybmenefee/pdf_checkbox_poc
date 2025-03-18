# Contributing to PDF Checkbox POC

Thank you for considering contributing to the PDF Checkbox POC project. This document provides guidelines and instructions to help you contribute effectively.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```
   git clone https://github.com/YOUR_USERNAME/pdf_checkbox_poc.git
   ```
3. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Copy `.env.template` to `.env` and fill in the required environment variables
6. Set up a MongoDB database for development

## Project Structure

- `/src` - Application source code
  - `/src/templates` - HTML templates
  - `/src/static` - Static assets (CSS, JS, images)
  - `/src/data` - Data files and test data
- `/docs` - Documentation
- `/tools` - Utility scripts for development and testing
- `/data` - Application data (templates, PDFs)

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Use docstrings for all functions, classes, and modules
- Write unit tests for new features
- Ensure all tests pass before submitting a pull request

## Testing

Run the test suite before submitting changes:

```
python src/run_tests.py
```

For visualization-specific tests:
```
python src/run_visualization_tests.py
```

## Pull Request Process

1. Create a feature branch for your changes
2. Make your changes following the coding standards
3. Add or update tests as necessary
4. Update documentation to reflect any changes
5. Ensure all tests pass
6. Submit a pull request with a clear description of the changes

## Development Tools

The `tools/` directory contains utility scripts that can help with development:

- `generate_test_pdf.py` - Creates test PDFs based on templates
- `setup_visualization.sh` - Sets up the visualization environment
- `debug_template_check.py` - Validates templates for potential issues

## Documentation

When adding new features or making significant changes, please update the relevant documentation:

- Update README.md for user-facing changes
- Update technical documentation in the docs/ directory
- Add comments to complex code sections

## Questions

If you have questions about contributing, please open an issue in the GitHub repository.

Thank you for your contributions! 