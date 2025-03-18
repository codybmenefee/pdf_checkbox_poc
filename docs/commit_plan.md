# Commit Plan for Static File Path Resolution

This document outlines the strategy for committing the static file path resolution changes to ensure clean, atomic commits that can be easily reviewed and reverted if needed.

## Branch Strategy

1. Create a new feature branch from main:
   ```
   git checkout -b fix/static-file-path-resolution
   ```

## Commits

### 1. Initial Fix for Static File Path Configuration

Commit the core changes that fix the static file path resolution issue:

```
git add src/app.py
git commit -m "fix: Resolve static file path configuration in Flask app

- Explicitly set app.static_folder and app.static_url_path
- Update static file serving routes to check multiple locations
- Improve logging for better diagnostics"
```

### 2. Add Tests for Static File Handling

Commit the new tests to validate the static file handling:

```
git add src/test_static_file_handling.py
git add src/run_tests.py
git add src/run_visualization_tests.py
git commit -m "test: Add comprehensive tests for static file handling

- Create TestStaticFileHandling for validating file access
- Update test runners to include static file tests
- Test file paths and 404 handling"
```

### 3. Add Documentation

Commit the documentation updates:

```
git add docs/static_file_configuration.md
git add README.md
git commit -m "docs: Add static file configuration documentation

- Document static file structure and configuration
- Add troubleshooting information
- Update README with static file information"
```

### 4. Clean Up and Optimize

Commit any final optimizations and clean-up changes:

```
git add src/app.py
git commit -m "refactor: Optimize static file handling code

- Reduce redundancy in path resolution
- Standardize logging levels
- Consolidate error handling"
```

### 5. Fix Route Conflict in UI API

Commit the fix for the route conflict between app.py and ui_api.py:

```
git add src/app.py src/ui_api.py src/test_static_file_handling.py
git commit -m "fix: Resolve route conflict for visualization files

- Fix conflicting route definitions between main app and UI API blueprint
- Rename UI API route to avoid conflict (/api/ui_visualizations/ instead of /api/visualizations/)
- Add test route and debug output to verify route registration
- Update tests to validate correct route handling"
```

## Pull Request

Create a pull request with the following details:

**Title**: Fix Static File Path Resolution for Visualizations

**Description**:
```
This PR resolves the issue where Flask was looking for static files in the wrong location, causing PDF visualizations and images to return 404 errors.

## Changes
- Fix Flask static_folder configuration to use project root
- Implement more robust file path resolution with fallbacks
- Add comprehensive tests for static file handling
- Add documentation for static file configuration

## Testing
1. All unit tests pass
2. Manual testing confirms visualizations now display properly
3. Tested with multiple browsers and file types

## Screenshots
[Include before/after screenshots of the PDF visualizations]
```

## Deployment Plan

After the PR is approved and merged:

1. Deploy to staging for final validation
2. Monitor logs for any static file 404 errors
3. Deploy to production during a low-traffic window
4. Verify all visualizations load correctly in production 