# Test Reorganization - Next Steps

## Current Status
- ✅ Created new test directory structure
- ✅ Created test_config.py for centralized test data path configuration
- ✅ Created path_setup.py to handle import path issues
- ✅ Updated run_all_tests.py and run_visualization_tests.py
- ✅ Updated test_visualization_feature.py in the new structure
- ✅ Updated test_static_paths.py in the new structure
- ✅ Created cleanup_old_tests.py to remove original test files after verification

## Next Steps for Test Reorganization

1. **Continue Refactoring Test Classes:**
   - Convert remaining test files to use the unittest framework consistently
   - Fix the TestFieldOverlay, TestE2EFieldVisualization, and TestE2ECheckboxVisualization classes
   - Create proper import statements in each test file to use the proper path setup

2. **Fix Database-Related Test Imports:**
   - Update imports in test_db_core.py, test_db_models.py, test_db_queries.py, and test_db_utils.py
   - They currently have ModuleNotFoundError for 'db_core' and 'db_utils'
   - Add proper imports to find these modules either from src/ or project root

3. **Review and Update CI/CD Configuration:**
   - Check if there are any CI/CD configurations that need to be updated to use the new test structure
   - Update any scripts or automation that references test files directly

4. **Test Data Management:**
   - Ensure test data (PDFs, templates) is correctly stored in tests/data
   - Update any hardcoded paths in tests to use the test_config.py helpers

5. **Implement Consolidation Tasks:**
   - Identify similar tests that can be merged
   - Standardize test naming conventions
   - Remove redundant test functions

6. **After Verification:**
   - Run python3 tests/cleanup_old_tests.py to remove original test files
   - The script will create backups before deletion

## Additional Recommendations
- Consider further separating integration tests from unit tests
- Add docstrings to all test functions for better documentation
- Create a test coverage report to identify gaps in test coverage

## Prompt for Next Agent

"Continue the test reorganization by:

1. Update the database-related tests (test_db_core.py, test_db_models.py, test_db_queries.py, test_db_utils.py) to fix import errors and use the new path structure
2. Convert the field overlay and E2E visualization test files to proper unittest TestCase classes
3. Implement test consolidation tasks - merge similar tests and standardize naming conventions
4. Ensure all test data is correctly managed through the test_config.py module
5. After verifying all tests pass (python3 tests/run_all_tests.py), run the cleanup script (python3 tests/cleanup_old_tests.py) to remove the original test files
6. Update any CI/CD configuration files to use the new test structure

To avoid breaking functionality, make incremental changes and test frequently. The goal is to have all tests passing in the new structure before completely removing the old test files." 