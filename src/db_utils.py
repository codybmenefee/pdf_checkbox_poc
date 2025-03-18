"""
Helper functions and utilities for database operations.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import datetime
import uuid
from bson import ObjectId

import pymongo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoJSONEncoder(json.JSONEncoder):
    """JSON encoder that can handle MongoDB-specific types."""
    
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a MongoDB document to be JSON-compatible.
    
    Args:
        doc: MongoDB document
        
    Returns:
        JSON-compatible dict
    """
    if not doc:
        return None
    
    result = {}
    
    # Process each field in the document
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime.datetime):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [
                serialize_mongo_doc(item) if isinstance(item, dict) else 
                str(item) if isinstance(item, ObjectId) else item
                for item in value
            ]
        elif isinstance(value, dict):
            result[key] = serialize_mongo_doc(value)
        else:
            result[key] = value
    
    return result


def serialize_mongo_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize a list of MongoDB documents to be JSON-compatible.
    
    Args:
        docs: List of MongoDB documents
        
    Returns:
        List of JSON-compatible dicts
    """
    return [serialize_mongo_doc(doc) for doc in docs]


def generate_uuid() -> str:
    """
    Generate a UUID.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def parse_date_param(date_str: Optional[str]) -> Optional[datetime.datetime]:
    """
    Parse a date string parameter.
    
    Args:
        date_str: Date string in ISO format
        
    Returns:
        Datetime object or None if invalid
    """
    if not date_str:
        return None
    
    try:
        return datetime.datetime.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid date format: {date_str} - {e}")
        return None


def validate_object_id(id_str: str) -> bool:
    """
    Validate if a string is a valid MongoDB ObjectId.
    
    Args:
        id_str: ID string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        return bool(ObjectId.is_valid(id_str))
    except Exception:
        return False


def format_query_results(results: List[Dict[str, Any]], 
                      include_fields: Optional[List[str]] = None,
                      exclude_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Format query results by including or excluding fields.
    
    Args:
        results: Query results
        include_fields: Optional list of fields to include
        exclude_fields: Optional list of fields to exclude
        
    Returns:
        Formatted results
    """
    if not results:
        return []
    
    formatted_results = []
    
    for result in results:
        # Apply exclusions first
        if exclude_fields:
            result = {k: v for k, v in result.items() if k not in exclude_fields}
        
        # Then apply inclusions if specified
        if include_fields:
            result = {k: result.get(k) for k in include_fields if k in result}
        
        # Add to results
        formatted_results.append(serialize_mongo_doc(result))
    
    return formatted_results


def paginate_results(results: List[Dict[str, Any]], 
                   page: int = 1, 
                   page_size: int = 100) -> Dict[str, Any]:
    """
    Paginate query results.
    
    Args:
        results: Query results
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Dict with pagination info and results
    """
    # Validate page parameters
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 100
    
    # Calculate pagination
    total_items = len(results)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    
    # Get page items
    page_items = results[start_idx:end_idx]
    
    # Return pagination info with results
    return {
        "page": page,
        "page_size": page_size,
        "total": total_items,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "data": page_items
    }


def build_sort_options(sort_by: Optional[str] = None, 
                     sort_order: Optional[str] = None) -> List[tuple]:
    """
    Build sort options for MongoDB queries.
    
    Args:
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        
    Returns:
        List of sort tuples
    """
    if not sort_by:
        return [("created_at", -1)]  # Default sort
    
    # Determine sort direction
    direction = -1 if sort_order and sort_order.lower() == 'desc' else 1
    
    return [(sort_by, direction)]


def extract_query_params(params: Dict[str, Any], 
                      allowed_params: List[str]) -> Dict[str, Any]:
    """
    Extract and validate query parameters.
    
    Args:
        params: Input parameters
        allowed_params: List of allowed parameter names
        
    Returns:
        Dict of validated parameters
    """
    return {k: v for k, v in params.items() if k in allowed_params} 


class DocumentSerializer:
    """Utility class for serializing and deserializing MongoDB documents."""
    
    @staticmethod
    def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize a MongoDB document for JSON response.
        
        Converts ObjectId to string and datetime to ISO format.
        
        Args:
            doc: MongoDB document
            
        Returns:
            Serialized document
        """
        if doc is None:
            return None
        
        if not doc:
            return {}
        
        result = {}
        
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime.datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = DocumentSerializer.serialize_document(value)
            elif isinstance(value, list):
                result[key] = [
                    DocumentSerializer.serialize_document(item) if isinstance(item, dict)
                    else str(item) if isinstance(item, ObjectId)
                    else item.isoformat() if isinstance(item, datetime.datetime)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def deserialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize a document back to MongoDB compatible types.
        
        Converts string to ObjectId and ISO format string to datetime where appropriate.
        
        Args:
            doc: Serialized document
            
        Returns:
            Deserialized document
        """
        if doc is None:
            return None
        
        if not doc:
            return {}
        
        result = {}
        
        for key, value in doc.items():
            if isinstance(value, str):
                # Try to convert to ObjectId if it matches the format
                if ObjectId.is_valid(value) and len(value) == 24:
                    result[key] = ObjectId(value)
                else:
                    # Try to convert to datetime if it's an ISO format
                    try:
                        result[key] = datetime.datetime.fromisoformat(value)
                    except ValueError:
                        result[key] = value
            elif isinstance(value, dict):
                result[key] = DocumentSerializer.deserialize_document(value)
            elif isinstance(value, list):
                result[key] = [
                    DocumentSerializer.deserialize_document(item) if isinstance(item, dict)
                    else ObjectId(item) if isinstance(item, str) and ObjectId.is_valid(item) and len(item) == 24
                    else datetime.datetime.fromisoformat(item) if isinstance(item, str) and "T" in item
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result


class ValidationUtility:
    """Utility class for validating data."""
    
    @staticmethod
    def validate_document_id(doc_id: str) -> bool:
        """Validate that a string is a valid document ID.
        
        Args:
            doc_id: Document ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not doc_id:
            return False
        
        return ObjectId.is_valid(doc_id)
    
    @staticmethod
    def validate_date_string(date_str: str) -> bool:
        """Validate that a string is a valid ISO format date.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not date_str:
            return False
        
        try:
            datetime.datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_template_data(data: Dict[str, Any]) -> bool:
        """Validate template data.
        
        Args:
            data: Template data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "description", "document_data", "checkboxes"]
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                return False
        
        # Check types
        if not isinstance(data["name"], str):
            return False
        
        if not isinstance(data["description"], str):
            return False
        
        if not isinstance(data["document_data"], dict):
            return False
        
        if not isinstance(data["checkboxes"], list):
            return False
        
        # Tags should be a list if present
        if "tags" in data and not isinstance(data["tags"], list):
            return False
        
        return True
    
    @staticmethod
    def validate_form_data(data: Dict[str, Any]) -> bool:
        """Validate form data.
        
        Args:
            data: Form data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["template_id", "name", "document_info", "field_values", "status"]
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                return False
        
        # Check types
        if not isinstance(data["template_id"], str):
            return False
        
        if not isinstance(data["name"], str):
            return False
        
        if not isinstance(data["document_info"], dict):
            return False
        
        if not isinstance(data["field_values"], list):
            return False
        
        if not isinstance(data["status"], str):
            return False
        
        # Validate status value
        valid_statuses = ["draft", "completed", "archived", "processing"]
        if data["status"] not in valid_statuses:
            return False
        
        return True


class DatabaseHelpers:
    """Helper class for common database operations."""
    
    @staticmethod
    def create_index_if_not_exists(
        collection,
        field_name: str,
        index_type: int = pymongo.ASCENDING,
        unique: bool = False
    ) -> None:
        """Create an index if it doesn't already exist.
        
        Args:
            collection: MongoDB collection
            field_name: Field to create index on
            index_type: Index type (ASCENDING/DESCENDING)
            unique: Whether the index should be unique
        """
        # Get existing indexes
        existing_indexes = collection.index_information()
        
        # Check if index already exists
        index_exists = False
        for index_name, index_info in existing_indexes.items():
            if len(index_info["key"]) == 1 and index_info["key"][0][0] == field_name:
                index_exists = True
                break
        
        # Create index if it doesn't exist
        if not index_exists:
            collection.create_index([(field_name, index_type)], unique=unique)
    
    @staticmethod
    def create_compound_index_if_not_exists(
        collection,
        fields: List[Tuple[str, int]],
        unique: bool = False
    ) -> None:
        """Create a compound index if it doesn't already exist.
        
        Args:
            collection: MongoDB collection
            fields: List of (field_name, direction) tuples
            unique: Whether the index should be unique
        """
        # Get existing indexes
        existing_indexes = collection.index_information()
        
        # Convert fields to a set of tuples for easier comparison
        fields_set = set((field, direction) for field, direction in fields)
        
        # Check if index already exists
        index_exists = False
        for index_name, index_info in existing_indexes.items():
            if len(index_info["key"]) == len(fields):
                existing_fields_set = set(index_info["key"])
                if existing_fields_set == fields_set:
                    index_exists = True
                    break
        
        # Create index if it doesn't exist
        if not index_exists:
            collection.create_index(fields, unique=unique)
    
    @staticmethod
    def ensure_collection_exists(
        db,
        collection_name: str
    ) -> None:
        """Ensure a collection exists in the database.
        
        Args:
            db: MongoDB database
            collection_name: Name of the collection
        """
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name) 