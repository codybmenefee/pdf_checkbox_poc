"""
Unit tests for the db_utils module.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import tempfile
import datetime

# Import path setup to handle imports from main project
import sys
# Add the tests directory to sys.path to allow importing from tests modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.path_setup import BASE_DIR, SRC_DIR
from tests.test_config import get_test_resource_path

# Now import the modules to test
sys.path.append(SRC_DIR)

from bson import ObjectId
import bson
import pymongo

from db_utils import (
    MongoJSONEncoder,
    serialize_mongo_doc,
    serialize_mongo_docs,
    generate_uuid,
    parse_date_param,
    validate_object_id,
    format_query_results,
    paginate_results,
    build_sort_options,
    extract_query_params,
    DocumentSerializer,
    ValidationUtility,
    DatabaseHelpers
)


class TestMongoJSONEncoder(unittest.TestCase):
    """Test cases for MongoJSONEncoder class."""

    def test_encode_objectid(self):
        """Test encoding ObjectId."""
        # Setup
        test_id = bson.ObjectId()
        test_obj = {"_id": test_id}
        
        # Execute
        result = json.dumps(test_obj, cls=MongoJSONEncoder)
        
        # Assert
        self.assertIn(f'"{str(test_id)}"', result)

    def test_encode_datetime(self):
        """Test encoding datetime."""
        # Setup
        test_date = datetime.datetime(2023, 1, 1, 12, 0, 0)
        test_obj = {"created_at": test_date}
        
        # Execute
        result = json.dumps(test_obj, cls=MongoJSONEncoder)
        
        # Assert
        self.assertIn('"2023-01-01T12:00:00"', result)

    def test_encode_regular_types(self):
        """Test encoding regular Python types."""
        # Setup
        test_obj = {
            "name": "Test",
            "value": 123,
            "is_active": True,
            "tags": ["a", "b", "c"],
            "nested": {"key": "value"}
        }
        
        # Execute & Assert (should not raise exception)
        json.dumps(test_obj, cls=MongoJSONEncoder)


class TestSerializeMongoDocs(unittest.TestCase):
    """Test cases for serialize_mongo_doc and serialize_mongo_docs functions."""

    def test_serialize_mongo_doc_objectid(self):
        """Test serializing a document with ObjectId."""
        # Setup
        test_id = bson.ObjectId()
        test_doc = {"_id": test_id}
        
        # Execute
        result = serialize_mongo_doc(test_doc)
        
        # Assert
        self.assertEqual(result["_id"], str(test_id))

    def test_serialize_mongo_doc_datetime(self):
        """Test serializing a document with datetime."""
        # Setup
        test_date = datetime.datetime(2023, 1, 1, 12, 0, 0)
        test_doc = {"created_at": test_date}
        
        # Execute
        result = serialize_mongo_doc(test_doc)
        
        # Assert
        self.assertEqual(result["created_at"], "2023-01-01T12:00:00")

    def test_serialize_mongo_doc_nested(self):
        """Test serializing a document with nested structures."""
        # Setup
        test_id = ObjectId("507f1f77bcf86cd799439011")
        nested_id = ObjectId("507f1f77bcf86cd799439012")
        test_doc = {
            "_id": test_id,
            "items": [
                {"item_id": nested_id, "name": "Item 1"},
                {"item_id": ObjectId("507f1f77bcf86cd799439013"), "name": "Item 2"}
            ]
        }
        
        # Execute
        result = serialize_mongo_doc(test_doc)
        
        # Assert
        self.assertEqual(result["_id"], str(test_id))
        self.assertEqual(result["items"][0]["item_id"], str(nested_id))
        self.assertTrue(isinstance(result["items"][1]["item_id"], str))
        self.assertEqual(result["items"][0]["name"], "Item 1")
        self.assertEqual(result["items"][1]["name"], "Item 2")

    def test_serialize_mongo_doc_none(self):
        """Test serializing None."""
        result = serialize_mongo_doc(None)
        self.assertIsNone(result)

    def test_serialize_mongo_docs(self):
        """Test serializing multiple MongoDB documents."""
        # Setup
        test_id1 = bson.ObjectId()
        test_id2 = bson.ObjectId()
        test_docs = [
            {"_id": test_id1, "name": "Doc 1"},
            {"_id": test_id2, "name": "Doc 2"}
        ]
        
        # Execute
        result = serialize_mongo_docs(test_docs)
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["_id"], str(test_id1))
        self.assertEqual(result[1]["_id"], str(test_id2))


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""

    @patch('db_utils.uuid.uuid4')
    def test_generate_uuid(self, mock_uuid):
        """Test generating a UUID."""
        # Setup
        mock_uuid.return_value = "test-uuid"
        
        # Execute
        from db_utils import generate_uuid
        result = generate_uuid()
        
        # Assert
        self.assertEqual(result, "test-uuid")

    def test_validate_object_id_valid(self):
        """Test validating a valid ObjectId."""
        valid_id = str(bson.ObjectId())
        self.assertTrue(validate_object_id(valid_id))

    def test_validate_object_id_invalid(self):
        """Test validating an invalid ObjectId."""
        invalid_id = "invalid-id"
        self.assertFalse(validate_object_id(invalid_id))

    def test_parse_date_param_valid(self):
        """Test parsing a valid date parameter."""
        date_str = "2023-01-01T12:00:00"
        result = parse_date_param(date_str)
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_parse_date_param_invalid(self):
        """Test parsing an invalid date parameter."""
        date_str = "invalid-date"
        result = parse_date_param(date_str)
        self.assertIsNone(result)

    def test_parse_date_param_none(self):
        """Test parsing None as a date parameter."""
        result = parse_date_param(None)
        self.assertIsNone(result)

    def test_format_query_results_include_fields(self):
        """Test formatting query results with included fields."""
        # Setup
        docs = [
            {"_id": "1", "name": "Doc 1", "value": 100, "tags": ["a", "b"]},
            {"_id": "2", "name": "Doc 2", "value": 200, "tags": ["c", "d"]}
        ]
        include_fields = ["_id", "name"]
        
        # Execute
        result = format_query_results(docs, include_fields=include_fields)
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(list(result[0].keys()), ["_id", "name"])
        self.assertEqual(list(result[1].keys()), ["_id", "name"])

    def test_format_query_results_exclude_fields(self):
        """Test formatting query results with excluded fields."""
        # Setup
        docs = [
            {"_id": "1", "name": "Doc 1", "value": 100, "tags": ["a", "b"]},
            {"_id": "2", "name": "Doc 2", "value": 200, "tags": ["c", "d"]}
        ]
        exclude_fields = ["tags"]
        
        # Execute
        result = format_query_results(docs, exclude_fields=exclude_fields)
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result[0].keys()), {"_id", "name", "value"})
        self.assertEqual(set(result[1].keys()), {"_id", "name", "value"})

    def test_format_query_results_empty(self):
        """Test formatting empty query results."""
        result = format_query_results([])
        self.assertEqual(result, [])

    def test_paginate_results(self):
        """Test paginating query results."""
        # Setup
        docs = [{"id": i} for i in range(1, 26)]  # 25 documents
        
        # Execute - Page 1, 10 items per page
        result = paginate_results(docs, page=1, page_size=10)
        
        # Assert
        self.assertEqual(result["total"], 25)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 10)
        self.assertEqual(result["total_pages"], 3)
        self.assertEqual(result["has_prev"], False)
        self.assertEqual(result["has_next"], True)
        self.assertEqual(len(result["data"]), 10)
        self.assertEqual(result["data"][0]["id"], 1)
        self.assertEqual(result["data"][9]["id"], 10)

    def test_paginate_results_last_page(self):
        """Test paginating to the last page of results."""
        # Setup
        docs = [{"id": i} for i in range(1, 26)]  # 25 documents
        
        # Execute - Page 3, 10 items per page
        result = paginate_results(docs, page=3, page_size=10)
        
        # Assert
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["has_prev"], True)
        self.assertEqual(result["has_next"], False)
        self.assertEqual(len(result["data"]), 5)  # Last page has 5 items
        self.assertEqual(result["data"][0]["id"], 21)
        self.assertEqual(result["data"][4]["id"], 25)

    def test_paginate_results_invalid_page(self):
        """Test paginating with an invalid page number."""
        # Setup
        docs = [{"id": i} for i in range(1, 11)]  # 10 documents
        
        # Execute - Page 0 should be treated as page 1
        result = paginate_results(docs, page=0, page_size=5)
        
        # Assert
        self.assertEqual(result["page"], 1)
        self.assertEqual(len(result["data"]), 5)
        self.assertEqual(result["data"][0]["id"], 1)

    def test_build_sort_options_default(self):
        """Test building default sort options."""
        result = build_sort_options()
        self.assertEqual(result, [("created_at", pymongo.DESCENDING)])

    def test_build_sort_options_asc(self):
        """Test building ascending sort options."""
        result = build_sort_options(sort_by="name", sort_order="asc")
        self.assertEqual(result, [("name", pymongo.ASCENDING)])

    def test_build_sort_options_desc(self):
        """Test building descending sort options."""
        result = build_sort_options(sort_by="value", sort_order="desc")
        self.assertEqual(result, [("value", pymongo.DESCENDING)])

    def test_extract_query_params(self):
        """Test extracting query parameters."""
        # Setup
        params = {
            "name": "Test",
            "value": 100,
            "invalid": "param",
            "tags": ["a", "b"],
            "none_value": None
        }
        valid_params = ["name", "value", "tags"]
        
        # Execute
        extracted = extract_query_params(params, valid_params)
        
        # Assert
        self.assertEqual(set(extracted.keys()), {"name", "value", "tags"})
        self.assertNotIn("invalid", extracted)
        self.assertNotIn("none_value", extracted)


class TestDocumentSerializer(unittest.TestCase):
    """Test cases for DocumentSerializer class."""
    
    def test_serialize_document(self):
        """Test serializing a document."""
        # Setup test document with ObjectId and datetime
        test_id = bson.ObjectId()
        test_date = datetime.datetime.utcnow()
        test_doc = {
            "_id": test_id,
            "name": "Test Document",
            "created_at": test_date,
            "nested": {
                "sub_id": test_id,
                "sub_date": test_date
            },
            "array": [
                {"arr_id": test_id, "arr_date": test_date},
                test_id,
                test_date
            ]
        }
        
        # Serialize the document
        result = DocumentSerializer.serialize_document(test_doc)
        
        # Check the result
        self.assertEqual(result["_id"], str(test_id))
        self.assertEqual(result["name"], "Test Document")
        self.assertIsInstance(result["created_at"], str)
        self.assertEqual(result["nested"]["sub_id"], str(test_id))
        self.assertIsInstance(result["nested"]["sub_date"], str)
        self.assertEqual(result["array"][0]["arr_id"], str(test_id))
        self.assertIsInstance(result["array"][0]["arr_date"], str)
        self.assertEqual(result["array"][1], str(test_id))
        self.assertIsInstance(result["array"][2], str)
    
    def test_serialize_document_empty(self):
        """Test serializing an empty document."""
        result = DocumentSerializer.serialize_document({})
        self.assertEqual(result, {})
    
    def test_deserialize_document(self):
        """Test deserializing a document."""
        # Setup serialized document
        test_id_str = str(bson.ObjectId())
        test_date_str = datetime.datetime.utcnow().isoformat()
        test_doc = {
            "_id": test_id_str,
            "name": "Test Document",
            "created_at": test_date_str,
            "nested": {
                "sub_id": test_id_str,
                "sub_date": test_date_str
            },
            "array": [
                {"arr_id": test_id_str, "arr_date": test_date_str},
                test_id_str,
                test_date_str
            ]
        }
        
        # Deserialize the document
        result = DocumentSerializer.deserialize_document(test_doc)
        
        # Check the result
        self.assertIsInstance(result["_id"], bson.ObjectId)
        self.assertEqual(str(result["_id"]), test_id_str)
        self.assertEqual(result["name"], "Test Document")
        self.assertIsInstance(result["created_at"], datetime.datetime)
        self.assertIsInstance(result["nested"]["sub_id"], bson.ObjectId)
        self.assertIsInstance(result["nested"]["sub_date"], datetime.datetime)
        self.assertIsInstance(result["array"][0]["arr_id"], bson.ObjectId)
        self.assertIsInstance(result["array"][0]["arr_date"], datetime.datetime)
        self.assertIsInstance(result["array"][1], bson.ObjectId)
        self.assertIsInstance(result["array"][2], datetime.datetime)
    
    def test_deserialize_document_invalid_objectid(self):
        """Test deserializing a document with invalid ObjectId."""
        test_doc = {
            "_id": "invalid-object-id",
            "name": "Test Document"
        }
        
        # This should not raise an exception, but keep the invalid format
        result = DocumentSerializer.deserialize_document(test_doc)
        self.assertEqual(result["_id"], "invalid-object-id")
    
    def test_deserialize_document_invalid_date(self):
        """Test deserializing a document with invalid date."""
        test_doc = {
            "_id": str(bson.ObjectId()),
            "created_at": "invalid-date-format"
        }
        
        # This should not raise an exception, but keep the invalid format
        result = DocumentSerializer.deserialize_document(test_doc)
        self.assertEqual(result["created_at"], "invalid-date-format")


if __name__ == '__main__':
    unittest.main() 