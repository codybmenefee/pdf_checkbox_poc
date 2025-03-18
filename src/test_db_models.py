"""
Unit tests for the db_models module.
"""

import unittest
from unittest.mock import patch, MagicMock
import datetime
import uuid
from bson import ObjectId

from db_core import DatabaseManager
from db_models import TemplateModel, FilledFormModel


class TestTemplateModel(unittest.TestCase):
    """Test cases for TemplateModel class."""

    def setUp(self):
        """Set up test environment."""
        # Mock database manager and collection
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.mock_collection = MagicMock()
        self.mock_db_manager.get_templates_collection.return_value = self.mock_collection
        
        # Create instance under test
        self.template_model = TemplateModel(self.mock_db_manager)
        
        # Define test data
        self.test_id = "550e8400-e29b-41d4-a716-446655440000"
        self.test_template = {
            "template_id": self.test_id,
            "name": "Test Template",
            "description": "Template for testing",
            "document_data": {"pages": [], "mime_type": "application/pdf"},
            "checkboxes": [
                {
                    "is_checked": True,
                    "confidence": 0.95,
                    "bounding_box": [
                        {"x": 100, "y": 100},
                        {"x": 120, "y": 100},
                        {"x": 120, "y": 120},
                        {"x": 100, "y": 120}
                    ]
                }
            ],
            "tags": ["test", "sample"],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }

    @patch('db_models.uuid.uuid4')
    def test_create(self, mock_uuid):
        """Test creating a template."""
        # Mock UUID generation
        mock_uuid.return_value = uuid.UUID(self.test_id)
        
        # Mock insertion result
        mock_result = MagicMock()
        mock_result.acknowledged = True
        self.mock_collection.insert_one.return_value = mock_result
        
        # Call the method under test
        result = self.template_model.create(
            name=self.test_template['name'],
            description=self.test_template['description'],
            document_data=self.test_template['document_data'],
            checkboxes=self.test_template['checkboxes'],
            tags=self.test_template['tags']
        )
        
        # Assert that the result contains expected values
        self.assertIsNotNone(result)
        self.assertEqual(result['template_id'], self.test_id)
        self.assertEqual(result['name'], self.test_template['name'])
        self.assertEqual(result['description'], self.test_template['description'])
        self.assertEqual(result['checkboxes'], self.test_template['checkboxes'])
        self.assertEqual(result['tags'], self.test_template['tags'])
        
        # Verify the collection method was called
        self.mock_collection.insert_one.assert_called_once()

    def test_create_failure(self):
        """Test failure when creating a template."""
        # Mock insertion result
        mock_result = MagicMock()
        mock_result.acknowledged = False
        self.mock_collection.insert_one.return_value = mock_result
        
        # Call the method under test
        result = self.template_model.create(
            name=self.test_template['name'],
            description=self.test_template['description'],
            document_data=self.test_template['document_data'],
            checkboxes=self.test_template['checkboxes']
        )
        
        # Assert that the result is None
        self.assertIsNone(result)
        
        # Verify the collection method was called
        self.mock_collection.insert_one.assert_called_once()

    def test_get(self):
        """Test retrieving a template."""
        # Mock find_one result
        self.mock_collection.find_one.return_value = self.test_template
        
        # Call the method under test
        result = self.template_model.get(self.test_id)
        
        # Assert that the result matches the test template
        self.assertEqual(result, self.test_template)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.find_one.assert_called_once_with({"template_id": self.test_id})

    def test_get_not_found(self):
        """Test retrieving a non-existent template."""
        # Mock find_one result
        self.mock_collection.find_one.return_value = None
        
        # Call the method under test
        result = self.template_model.get(self.test_id)
        
        # Assert that the result is None
        self.assertIsNone(result)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.find_one.assert_called_once_with({"template_id": self.test_id})

    def test_list(self):
        """Test listing templates."""
        # Mock find result
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [self.test_template]
        self.mock_collection.find.return_value = mock_cursor
        
        # Call the method under test
        results = self.template_model.list(tags=["test"])
        
        # Assert that the results contain the test template
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_template)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.find.assert_called_once_with({"tags": {"$all": ["test"]}})
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(100)

    def test_update(self):
        """Test updating a template."""
        # Mock find_one and update_one results
        self.mock_collection.find_one.return_value = self.test_template
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Prepare updates
        updates = {
            "name": "Updated Template",
            "description": "Updated description"
        }
        
        # Call the method under test
        result = self.template_model.update(self.test_id, updates)
        
        # Assert the result matches the test template (as returned by the get method)
        self.assertEqual(result, self.test_template)
        
        # Verify the collection methods were called with correct arguments
        self.mock_collection.find_one.assert_called_with({"template_id": self.test_id})
        self.mock_collection.update_one.assert_called_once()
        args, kwargs = self.mock_collection.update_one.call_args
        self.assertEqual(args[0], {"template_id": self.test_id})
        self.assertIn("$set", args[1])
        self.assertIn("name", args[1]["$set"])
        self.assertIn("description", args[1]["$set"])
        self.assertIn("updated_at", args[1]["$set"])

    def test_update_not_found(self):
        """Test updating a non-existent template."""
        # Mock find_one result
        self.mock_collection.find_one.return_value = None
        
        # Prepare updates
        updates = {
            "name": "Updated Template",
            "description": "Updated description"
        }
        
        # Call the method under test
        result = self.template_model.update(self.test_id, updates)
        
        # Assert the result is None
        self.assertIsNone(result)
        
        # Verify the find_one method was called, but update_one was not
        self.mock_collection.find_one.assert_called_once_with({"template_id": self.test_id})
        self.mock_collection.update_one.assert_not_called()

    def test_delete(self):
        """Test deleting a template."""
        # Mock delete_one result
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        self.mock_collection.delete_one.return_value = mock_result
        
        # Call the method under test
        result = self.template_model.delete(self.test_id)
        
        # Assert the result is True
        self.assertTrue(result)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.delete_one.assert_called_once_with({"template_id": self.test_id})

    def test_delete_not_found(self):
        """Test deleting a non-existent template."""
        # Mock delete_one result
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        self.mock_collection.delete_one.return_value = mock_result
        
        # Call the method under test
        result = self.template_model.delete(self.test_id)
        
        # Assert the result is False
        self.assertFalse(result)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.delete_one.assert_called_once_with({"template_id": self.test_id})

    def test_add_tag(self):
        """Test adding a tag to a template."""
        # Mock find_one and update_one results
        self.mock_collection.find_one.return_value = self.test_template
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Call the method under test
        result = self.template_model.add_tag(self.test_id, "new-tag")
        
        # Assert the result is True
        self.assertTrue(result)
        
        # Verify the collection methods were called with correct arguments
        self.mock_collection.find_one.assert_called_once_with({"template_id": self.test_id})
        self.mock_collection.update_one.assert_called_once()
        args, kwargs = self.mock_collection.update_one.call_args
        self.assertEqual(args[0], {"template_id": self.test_id})
        self.assertIn("$push", args[1])
        self.assertIn("tags", args[1]["$push"])
        self.assertEqual(args[1]["$push"]["tags"], "new-tag")

    def test_remove_tag(self):
        """Test removing a tag from a template."""
        # Mock find_one and update_one results
        self.mock_collection.find_one.return_value = self.test_template
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Call the method under test
        result = self.template_model.remove_tag(self.test_id, "test")
        
        # Assert the result is True
        self.assertTrue(result)
        
        # Verify the collection methods were called with correct arguments
        self.mock_collection.find_one.assert_called_once_with({"template_id": self.test_id})
        self.mock_collection.update_one.assert_called_once()
        args, kwargs = self.mock_collection.update_one.call_args
        self.assertEqual(args[0], {"template_id": self.test_id})
        self.assertIn("$pull", args[1])
        self.assertIn("tags", args[1]["$pull"])
        self.assertEqual(args[1]["$pull"]["tags"], "test")


class TestFilledFormModel(unittest.TestCase):
    """Test cases for FilledFormModel class."""

    def setUp(self):
        """Set up test environment."""
        # Mock database manager and collection
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.mock_collection = MagicMock()
        self.mock_db_manager.get_filled_forms_collection.return_value = self.mock_collection
        
        # Create instance under test
        self.form_model = FilledFormModel(self.mock_db_manager)
        
        # Define test data
        self.test_id = "660e8400-e29b-41d4-a716-446655440001"
        self.test_template_id = "550e8400-e29b-41d4-a716-446655440000"
        self.test_form = {
            "form_id": self.test_id,
            "template_id": self.test_template_id,
            "name": "Test Form",
            "document_info": {"filename": "test.pdf", "file_size": 1000},
            "field_values": [
                {
                    "field_id": "field_1",
                    "value": True
                }
            ],
            "status": "draft",
            "exports": [],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }

    @patch('db_models.uuid.uuid4')
    def test_create(self, mock_uuid):
        """Test creating a filled form."""
        # Mock UUID generation
        mock_uuid.return_value = uuid.UUID(self.test_id)
        
        # Mock insertion result
        mock_result = MagicMock()
        mock_result.acknowledged = True
        self.mock_collection.insert_one.return_value = mock_result
        
        # Call the method under test
        result = self.form_model.create(
            template_id=self.test_template_id,
            name=self.test_form['name'],
            document_info=self.test_form['document_info'],
            field_values=self.test_form['field_values']
        )
        
        # Assert that the result contains expected values
        self.assertIsNotNone(result)
        self.assertEqual(result['form_id'], self.test_id)
        self.assertEqual(result['template_id'], self.test_template_id)
        self.assertEqual(result['name'], self.test_form['name'])
        self.assertEqual(result['document_info'], self.test_form['document_info'])
        self.assertEqual(result['field_values'], self.test_form['field_values'])
        self.assertEqual(result['status'], "draft")
        
        # Verify the collection method was called
        self.mock_collection.insert_one.assert_called_once()

    def test_get(self):
        """Test retrieving a filled form."""
        # Mock find_one result
        self.mock_collection.find_one.return_value = self.test_form
        
        # Call the method under test
        result = self.form_model.get(self.test_id)
        
        # Assert that the result matches the test form
        self.assertEqual(result, self.test_form)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.find_one.assert_called_once_with({"form_id": self.test_id})

    def test_list(self):
        """Test listing filled forms."""
        # Mock find result
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [self.test_form]
        self.mock_collection.find.return_value = mock_cursor
        
        # Call the method under test
        results = self.form_model.list(template_id=self.test_template_id, status="draft")
        
        # Assert that the results contain the test form
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_form)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.find.assert_called_once_with(
            {"template_id": self.test_template_id, "status": "draft"}
        )
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(100)

    def test_update_field_values(self):
        """Test updating field values for a filled form."""
        # Mock find_one and update_one results
        self.mock_collection.find_one.return_value = self.test_form
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Prepare updated field values
        updated_fields = [
            {
                "field_id": "field_1",
                "value": False  # Changed from True
            },
            {
                "field_id": "field_2",
                "value": "New Value"
            }
        ]
        
        # Call the method under test
        result = self.form_model.update_field_values(self.test_id, updated_fields)
        
        # Assert the result matches the test form (as returned by the get method)
        self.assertEqual(result, self.test_form)
        
        # Verify the collection methods were called with correct arguments
        self.mock_collection.find_one.assert_any_call({"form_id": self.test_id})
        self.mock_collection.update_one.assert_called_once()
        args, kwargs = self.mock_collection.update_one.call_args
        self.assertEqual(args[0], {"form_id": self.test_id})
        self.assertIn("$set", args[1])
        self.assertIn("field_values", args[1]["$set"])
        self.assertEqual(args[1]["$set"]["field_values"], updated_fields)

    def test_update_status(self):
        """Test updating status for a filled form."""
        # Mock find_one and update_one results
        self.mock_collection.find_one.return_value = self.test_form
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Call the method under test
        result = self.form_model.update_status(self.test_id, "completed")
        
        # Assert the result matches the test form (as returned by the get method)
        self.assertEqual(result, self.test_form)
        
        # Verify the collection methods were called with correct arguments
        self.mock_collection.find_one.assert_any_call({"form_id": self.test_id})
        self.mock_collection.update_one.assert_called_once()
        args, kwargs = self.mock_collection.update_one.call_args
        self.assertEqual(args[0], {"form_id": self.test_id})
        self.assertIn("$set", args[1])
        self.assertIn("status", args[1]["$set"])
        self.assertEqual(args[1]["$set"]["status"], "completed")

    def test_add_export_record(self):
        """Test adding an export record to a filled form."""
        # Mock find_one and update_one results
        self.mock_collection.find_one.return_value = self.test_form
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Call the method under test
        result = self.form_model.add_export_record(
            self.test_id, "s3://bucket/test.pdf", "success"
        )
        
        # Assert the result matches the test form (as returned by the get method)
        self.assertEqual(result, self.test_form)
        
        # Verify the collection methods were called with correct arguments
        self.mock_collection.find_one.assert_any_call({"form_id": self.test_id})
        self.mock_collection.update_one.assert_called_once()
        args, kwargs = self.mock_collection.update_one.call_args
        self.assertEqual(args[0], {"form_id": self.test_id})
        self.assertIn("$push", args[1])
        self.assertIn("exports", args[1]["$push"])
        self.assertEqual(args[1]["$push"]["exports"]["destination"], "s3://bucket/test.pdf")
        self.assertEqual(args[1]["$push"]["exports"]["status"], "success")

    def test_delete(self):
        """Test deleting a filled form."""
        # Mock delete_one result
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        self.mock_collection.delete_one.return_value = mock_result
        
        # Call the method under test
        result = self.form_model.delete(self.test_id)
        
        # Assert the result is True
        self.assertTrue(result)
        
        # Verify the collection method was called with correct arguments
        self.mock_collection.delete_one.assert_called_once_with({"form_id": self.test_id})


if __name__ == '__main__':
    unittest.main() 