# Test Organization

This directory contains all tests for the PDF Checkbox POC project. The tests are organized as follows:

## Directory Structure

- `tests/`
  - `unit/` - Unit tests for individual components
    - `visualization/` - Tests specific to visualization features
  - `integration/` - Integration tests for multiple components
  - `tools/` - Test utility scripts
  - `data/` - Test data files
    - `pdfs/` - PDF files used for testing
    - `templates/` - Template files used for testing

## Running Tests

You can run tests using the main test runner script:

```bash
# Run all tests
python tests/run_all_tests.py

# Run only unit tests
python tests/run_all_tests.py --unit

# Run only integration tests
python tests/run_all_tests.py --integration

# Run only visualization tests
python tests/run_all_tests.py --visualization

# Run specific test files
python tests/run_all_tests.py --specific tests/unit/test_specific_file.py
```

## Test Data

Test data is stored in the `tests/data` directory:
- PDF files are in `tests/data/pdfs/`
- Template files are in `tests/data/templates/`

To access test data in your tests, use the functions in `tests/test_config.py`.

## Test Utilities

Utility scripts for testing are stored in the `tests/tools` directory. These include:
- `generate_test_pdf.py` - Generate test PDFs
- `generate_placeholders.py` - Generate placeholder data
- `debug_template_check.py` - Debug template issues
- `run_field_test.sh` - Run field tests
- `test_visualization_forms.sh` - Test visualization forms
- `create_test_form.py` - Create test forms
- `extract_pdf_page.py` - Extract pages from PDFs 