# Static File Path Resolution Fix

This document explains how the static file path resolution issue in the PDF form visualization tool was fixed.

## Issue Description

The application was experiencing a path resolution issue where Flask was looking for static files at:
```
/Users/codymenefee/Downloads/pdf_checkbox_poc/src/static/visualizations/...
```

But the files were actually at:
```
/Users/codymenefee/Downloads/pdf_checkbox_poc/static/visualizations/...
```

This resulted in 404 errors for static files, particularly visualization images.

## Solution Applied

The following changes were made to fix the issue:

1. **Improved static folder configuration** in `app.py`:
   - Explicitly set the static folder to the project root's `static` directory
   - Added detailed logging of static folder configuration

2. **Added a static file synchronization mechanism**:
   - Created a `sync_static_folders()` function that copies files from `src/static` to the root `static` directory
   - This ensures all static files are available in the expected location

3. **Enhanced static file route handlers**:
   - Updated route handlers to check multiple possible locations for static files
   - Added fallback paths to ensure files can be found in either location

4. **Created a test script** (`test_static_paths.py`):
   - Verifies static file access works correctly
   - Tests visualization file access
   - Confirms static file synchronization is working

## How to Test

1. Start the Flask application:
   ```bash
   python3 -m src.app --debug
   ```

2. Run the test script to verify the fix:
   ```bash
   python3 test_static_paths.py
   ```

3. Check the following URLs in your browser:
   - `http://localhost:5000/static/images/loading-placeholder.png` - Should display the loading placeholder
   - `http://localhost:5000/static_debug` - Will show details about static file configuration

## Technical Details

The key changes were:

1. In `app.py`, Flask's static folder is now explicitly set:
   ```python
   static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
   app.static_folder = static_folder
   app.static_url_path = '/static'
   ```

2. Added synchronization function to copy files from `src/static` to the root `static` directory:
   ```python
   def sync_static_folders():
       """Sync files from src/static to the app's configured static folder."""
       src_static = os.path.join(os.path.dirname(__file__), 'static')
       
       if os.path.exists(src_static) and os.path.isdir(src_static):
           # Copy files from src/static to app.static_folder
           # ...
   ```

3. Updated route handlers to check multiple locations:
   ```python
   potential_paths = [
       os.path.join(app.static_folder, 'visualizations', visualization_id),
       os.path.join(os.getcwd(), 'static', 'visualizations', visualization_id),
       os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'visualizations', visualization_id),
       # ...
   ]
   ```

These changes ensure that static files are correctly served from the application root rather than inside the src directory. 