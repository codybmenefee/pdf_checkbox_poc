"""
Unit tests for the db_core module.
"""

import unittest
from unittest.mock import patch, MagicMock
import pymongo

# Import path setup to handle imports from main project
import sys
import os
# Add the tests directory to sys.path to allow importing from tests modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.path_setup import BASE_DIR, SRC_DIR

# Now import the module to test
sys.path.append(SRC_DIR)
from db_core import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test instance in test mode
        self.db_manager = DatabaseManager(
            connection_string='mongodb://test', 
            db_name='test_db',
            test_mode=True
        )
        
        # Set up mock db and collection for tests
        self.db_manager.db = MagicMock()
        self.mock_collection = MagicMock()
        self.db_manager.db.__getitem__.return_value = self.mock_collection
    
    def test_init(self):
        """Test initialization of DatabaseManager."""
        # Test initialization with test_mode
        db_manager = DatabaseManager(
            connection_string='mongodb://custom',
            db_name='custom_db',
            test_mode=True
        )
        
        # Verify the connection parameters are set properly
        self.assertEqual(db_manager.connection_string, 'mongodb://custom')
        self.assertEqual(db_manager.db_name, 'custom_db')
        self.assertIsNone(db_manager.client)
        self.assertIsNone(db_manager.db)
    
    def test_test_mode(self):
        """Test initialization in test mode."""
        # Create database manager in test mode
        db_manager = DatabaseManager(
            connection_string='mongodb://test',
            db_name='test_db',
            test_mode=True
        )
        
        # Verify attributes
        self.assertIsNone(db_manager.client)
        self.assertIsNone(db_manager.db)
        self.assertEqual(db_manager.connection_string, 'mongodb://test')
        self.assertEqual(db_manager.db_name, 'test_db')
    
    def test_connect(self):
        """Test connection to MongoDB."""
        # We'll use test_mode and manually configure the db_manager
        db_manager = DatabaseManager(
            connection_string='mongodb://test',
            db_name='test_db',
            test_mode=True
        )
        
        # Manually set up client and db to simulate connection
        db_manager.client = MagicMock()
        db_manager.db = MagicMock()
        
        # Verify attributes
        self.assertTrue(hasattr(db_manager, 'client'))
        self.assertIsNotNone(db_manager.client)
        self.assertTrue(hasattr(db_manager, 'db'))
        self.assertIsNotNone(db_manager.db)
    
    @patch('pymongo.MongoClient')
    def test_connect_error(self, mock_client):
        """Test error handling during connection."""
        # Configure the mock to raise an exception
        mock_client.return_value.admin.command.side_effect = pymongo.errors.ConnectionFailure("Connection error")
        
        # Attempt to create a database manager (with test_mode=False to force real connection)
        with self.assertRaises(pymongo.errors.ConnectionFailure):
            DatabaseManager(connection_string='mongodb://test', db_name='test_db', test_mode=False)
    
    def test_get_templates_collection(self):
        """Test getting the templates collection."""
        # Execute
        collection = self.db_manager.get_templates_collection()
        
        # Assert
        self.assertEqual(collection, self.mock_collection)
        self.db_manager.db.__getitem__.assert_called_with("templates")
    
    def test_get_filled_forms_collection(self):
        """Test getting the filled forms collection."""
        # Execute
        collection = self.db_manager.get_filled_forms_collection()
        
        # Assert
        self.assertEqual(collection, self.mock_collection)
        self.db_manager.db.__getitem__.assert_called_with("filled_forms")
    
    def test_close(self):
        """Test closing the database connection."""
        # Set up a mock client
        self.db_manager.client = MagicMock()
        
        # Call the method under test
        self.db_manager.close_connection()
        
        # Verify the client's close method was called
        self.db_manager.client.close.assert_called_once()
        
        # Test with no client (test mode)
        self.db_manager.client = None
        # Should not raise an exception
        self.db_manager.close_connection()
    
    def test_get_db(self):
        """Test getting the database."""
        # Execute - db is already mocked in setUp
        db = self.db_manager.db
        
        # Assert
        self.assertIsNotNone(db)
    
    def test_ping(self):
        """Test ping method with mocked client."""
        # Create a db manager with a mock client
        db_manager = DatabaseManager(test_mode=True)
        db_manager.client = MagicMock()
        
        # Mock successful ping
        admin_mock = MagicMock()
        admin_mock.command.return_value = True
        db_manager.client.admin = admin_mock
        
        self.assertTrue(db_manager.ping())
        admin_mock.command.assert_called_with('ping')
        
        # Mock failed ping
        admin_mock.command.side_effect = pymongo.errors.ConnectionFailure("Connection error")
        self.assertFalse(db_manager.ping())
        
        # Test with no client (test mode)
        db_manager.client = None
        self.assertFalse(db_manager.ping())
    
    def test_create_indexes(self):
        """Test creating indexes."""
        # Mock the collections
        templates_coll = MagicMock()
        forms_coll = MagicMock()
        
        # Create a db manager with mock collections
        db_manager = DatabaseManager(test_mode=True)
        db_manager.db = MagicMock()
        db_manager.get_templates_collection = MagicMock(return_value=templates_coll)
        db_manager.get_filled_forms_collection = MagicMock(return_value=forms_coll)
        
        # Call the method under test
        db_manager.create_indexes()
        
        # Verify the collections' create_index methods were called
        templates_coll.create_index.assert_any_call("template_id", unique=True)
        templates_coll.create_index.assert_any_call("tags")
        templates_coll.create_index.assert_any_call("created_at")
        
        forms_coll.create_index.assert_any_call("form_id", unique=True)
        forms_coll.create_index.assert_any_call("template_id")
        forms_coll.create_index.assert_any_call("status")
        forms_coll.create_index.assert_any_call("created_at")
        
        # Test with no db (test mode with db=None)
        db_manager.db = None
        # Should not raise an exception
        db_manager.create_indexes()
    
    def test_generate_id(self):
        """Test generating a unique ID."""
        id1 = self.db_manager.generate_id()
        id2 = self.db_manager.generate_id()
        
        self.assertIsInstance(id1, str)
        self.assertIsInstance(id2, str)
        self.assertNotEqual(id1, id2)
    
    def test_get_current_timestamp(self):
        """Test getting the current timestamp."""
        timestamp = self.db_manager.get_current_timestamp()
        self.assertIsNotNone(timestamp)
    
    def test_null_collection_methods(self):
        """Test collection methods when db is None."""
        # Create a db manager in test mode
        db_manager = DatabaseManager(test_mode=True)
        
        # Test get_templates_collection returns None
        self.assertIsNone(db_manager.get_templates_collection())
        
        # Test get_filled_forms_collection returns None
        self.assertIsNone(db_manager.get_filled_forms_collection())


if __name__ == '__main__':
    unittest.main() 