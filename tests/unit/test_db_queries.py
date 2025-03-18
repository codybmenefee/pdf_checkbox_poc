"""
Unit tests for the db_queries module.
"""

import unittest
from unittest.mock import patch, MagicMock
import datetime
import pymongo
from bson import ObjectId

# Import path setup to handle imports from main project
import sys
import os
# Add the tests directory to sys.path to allow importing from tests modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.path_setup import BASE_DIR, SRC_DIR

# Now import the modules to test
sys.path.append(SRC_DIR)

from db_core import DatabaseManager
from db_models import TemplateModel, FilledFormModel
from db_queries import QueryBuilder, ComplexQueries


class TestQueryBuilder(unittest.TestCase):
    """Test cases for QueryBuilder class."""

    def test_build_template_filter_empty(self):
        """Test building an empty template filter."""
        query = QueryBuilder.build_template_filter()
        self.assertEqual(query, {})

    def test_build_template_filter_tags(self):
        """Test building a template filter with tags."""
        tags = ["test", "sample"]
        query = QueryBuilder.build_template_filter(tags=tags)
        self.assertEqual(query, {"tags": {"$all": tags}})

    def test_build_template_filter_name(self):
        """Test building a template filter with name contains."""
        name_contains = "Test Template"
        query = QueryBuilder.build_template_filter(name_contains=name_contains)
        self.assertEqual(query, {"name": {"$regex": name_contains, "$options": "i"}})

    def test_build_template_filter_dates(self):
        """Test building a template filter with date range."""
        created_after = datetime.datetime(2023, 1, 1)
        created_before = datetime.datetime(2023, 12, 31)
        query = QueryBuilder.build_template_filter(
            created_after=created_after, created_before=created_before
        )
        self.assertEqual(query, {
            "created_at": {
                "$gte": created_after,
                "$lte": created_before
            }
        })

    def test_build_template_filter_all(self):
        """Test building a template filter with all parameters."""
        tags = ["test", "sample"]
        name_contains = "Test Template"
        created_after = datetime.datetime(2023, 1, 1)
        created_before = datetime.datetime(2023, 12, 31)
        query = QueryBuilder.build_template_filter(
            tags=tags,
            name_contains=name_contains,
            created_after=created_after,
            created_before=created_before
        )
        self.assertEqual(query, {
            "tags": {"$all": tags},
            "name": {"$regex": name_contains, "$options": "i"},
            "created_at": {
                "$gte": created_after,
                "$lte": created_before
            }
        })

    def test_build_form_filter_empty(self):
        """Test building an empty form filter."""
        query = QueryBuilder.build_form_filter()
        self.assertEqual(query, {})

    def test_build_form_filter_template_id(self):
        """Test building a form filter with template ID."""
        template_id = "test-template-id"
        query = QueryBuilder.build_form_filter(template_id=template_id)
        self.assertEqual(query, {"template_id": template_id})

    def test_build_form_filter_status(self):
        """Test building a form filter with status."""
        status = "draft"
        query = QueryBuilder.build_form_filter(status=status)
        self.assertEqual(query, {"status": status})

    def test_build_form_filter_name(self):
        """Test building a form filter with name contains."""
        name_contains = "Test Form"
        query = QueryBuilder.build_form_filter(name_contains=name_contains)
        self.assertEqual(query, {"name": {"$regex": name_contains, "$options": "i"}})

    def test_build_form_filter_dates(self):
        """Test building a form filter with date range."""
        created_after = datetime.datetime(2023, 1, 1)
        created_before = datetime.datetime(2023, 12, 31)
        query = QueryBuilder.build_form_filter(
            created_after=created_after, created_before=created_before
        )
        self.assertEqual(query, {
            "created_at": {
                "$gte": created_after,
                "$lte": created_before
            }
        })

    def test_build_form_filter_all(self):
        """Test building a form filter with all parameters."""
        template_id = "test-template-id"
        status = "draft"
        name_contains = "Test Form"
        created_after = datetime.datetime(2023, 1, 1)
        created_before = datetime.datetime(2023, 12, 31)
        query = QueryBuilder.build_form_filter(
            template_id=template_id,
            status=status,
            name_contains=name_contains,
            created_after=created_after,
            created_before=created_before
        )
        self.assertEqual(query, {
            "template_id": template_id,
            "status": status,
            "name": {"$regex": name_contains, "$options": "i"},
            "created_at": {
                "$gte": created_after,
                "$lte": created_before
            }
        })


class TestComplexQueries(unittest.TestCase):
    """Test cases for ComplexQueries class."""

    def setUp(self):
        """Set up test environment."""
        # Mock database manager, template model, and form model
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.mock_template_model = MagicMock(spec=TemplateModel)
        self.mock_form_model = MagicMock(spec=FilledFormModel)
        
        # Define mock collections
        self.mock_templates_collection = MagicMock()
        self.mock_forms_collection = MagicMock()
        
        # Configure mocks
        self.mock_db_manager.get_templates_collection.return_value = self.mock_templates_collection
        self.mock_db_manager.get_filled_forms_collection.return_value = self.mock_forms_collection
        
        # Patch TemplateModel and FilledFormModel to use our mocks
        with patch('db_queries.TemplateModel', return_value=self.mock_template_model):
            with patch('db_queries.FilledFormModel', return_value=self.mock_form_model):
                # Create instance under test
                self.complex_queries = ComplexQueries(self.mock_db_manager)
        
        # Define test data
        self.test_template_id = "test-template-id"
        self.test_template = {
            "template_id": self.test_template_id,
            "name": "Test Template",
            "description": "Template for testing",
            "document_data": {"pages": [], "mime_type": "application/pdf"},
            "checkboxes": [],
            "tags": ["test", "sample"],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        
        self.test_form = {
            "form_id": "test-form-id",
            "template_id": self.test_template_id,
            "name": "Test Form",
            "document_info": {"filename": "test.pdf", "file_size": 1000},
            "field_values": [],
            "status": "draft",
            "exports": [],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }

    def test_get_template_with_filled_forms(self):
        """Test getting a template with its filled forms."""
        # Mock template and form models
        self.mock_template_model.get.return_value = self.test_template
        self.mock_form_model.list.return_value = [self.test_form]
        
        # Call the method under test
        result = self.complex_queries.get_template_with_filled_forms(self.test_template_id)
        
        # Assert the result contains the template and forms
        self.assertIsNotNone(result)
        self.assertEqual(result["template"], self.test_template)
        self.assertEqual(len(result["filled_forms"]), 1)
        self.assertEqual(result["filled_forms"][0], self.test_form)
        
        # Verify the model methods were called with correct arguments
        self.mock_template_model.get.assert_called_once_with(self.test_template_id)
        self.mock_form_model.list.assert_called_once_with(template_id=self.test_template_id)

    def test_get_template_with_filled_forms_not_found(self):
        """Test getting a non-existent template with filled forms."""
        # Mock template model to return None
        self.mock_template_model.get.return_value = None
        
        # Call the method under test
        result = self.complex_queries.get_template_with_filled_forms(self.test_template_id)
        
        # Assert the result is None
        self.assertIsNone(result)
        
        # Verify the template model get method was called, but form model list was not
        self.mock_template_model.get.assert_called_once_with(self.test_template_id)
        self.mock_form_model.list.assert_not_called()

    def test_search_templates(self):
        """Test searching templates by name or tags."""
        # Mock templates collection find
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [self.test_template]
        self.mock_templates_collection.find.return_value = mock_cursor
        
        # Call the method under test
        results = self.complex_queries.search_templates(
            search_term="Test",
            tags=["test"],
            skip=0,
            limit=10
        )
        
        # Assert the results contain the test template
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_template)
        
        # Verify the collection method was called with correct arguments
        expected_query = {
            "name": {"$regex": "Test", "$options": "i"},
            "tags": {"$all": ["test"]}
        }
        self.mock_templates_collection.find.assert_called_once_with(expected_query)
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(10)

    def test_get_form_statistics(self):
        """Test getting form statistics."""
        # Mock aggregate result
        self.mock_forms_collection.aggregate.return_value = [
            {"_id": "draft", "count": 5},
            {"_id": "completed", "count": 3}
        ]
        
        # Call the method under test
        stats = self.complex_queries.get_form_statistics(template_id=self.test_template_id)
        
        # Assert the statistics are calculated correctly
        self.assertEqual(stats["total"], 8)
        self.assertEqual(stats["by_status"]["draft"], 5)
        self.assertEqual(stats["by_status"]["completed"], 3)
        
        # Verify the collection method was called with correct arguments
        self.mock_forms_collection.aggregate.assert_called_once()
        pipeline_arg = self.mock_forms_collection.aggregate.call_args[0][0]
        self.assertEqual(len(pipeline_arg), 2)
        self.assertEqual(pipeline_arg[0]["$match"], {"template_id": self.test_template_id})
        self.assertEqual(pipeline_arg[1]["$group"]["_id"], "$status")
        self.assertEqual(pipeline_arg[1]["$group"]["count"]["$sum"], 1)

    def test_get_templates_with_form_counts(self):
        """Test getting templates with form counts."""
        # Mock template model list
        self.mock_template_model.list.return_value = [self.test_template]
        
        # Mock forms collection aggregate
        self.mock_forms_collection.aggregate.return_value = [
            {"_id": self.test_template_id, "count": 5}
        ]
        
        # Call the method under test
        results = self.complex_queries.get_templates_with_form_counts(skip=0, limit=10)
        
        # Assert the results contain the template with form count
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["template_id"], self.test_template_id)
        self.assertEqual(results[0]["form_count"], 5)
        
        # Verify the model and collection methods were called with correct arguments
        self.mock_template_model.list.assert_called_once_with(skip=0, limit=10)
        self.mock_forms_collection.aggregate.assert_called_once()
        pipeline_arg = self.mock_forms_collection.aggregate.call_args[0][0]
        self.assertEqual(len(pipeline_arg), 2)
        self.assertEqual(pipeline_arg[0]["$match"], {"template_id": self.test_template_id})
        self.assertEqual(pipeline_arg[1]["$group"]["_id"], "$template_id")
        self.assertEqual(pipeline_arg[1]["$group"]["count"]["$sum"], 1)

    def test_find_forms_with_field_value(self):
        """Test finding forms with a specific field value."""
        # Mock forms collection find
        self.mock_forms_collection.find.return_value = [self.test_form]
        
        # Call the method under test
        results = self.complex_queries.find_forms_with_field_value(
            field_key="field_1",
            field_value=True,
            template_id=self.test_template_id
        )
        
        # Assert the results contain the test form
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_form)
        
        # Verify the collection method was called with correct arguments
        expected_query = {
            "field_values": {
                "$elemMatch": {
                    "key": "field_1",
                    "value": True
                }
            },
            "template_id": self.test_template_id
        }
        self.mock_forms_collection.find.assert_called_once_with(expected_query)


if __name__ == '__main__':
    unittest.main() 