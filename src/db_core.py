"""
Core database functionality for the PDF Checkbox POC project.
Provides the DatabaseManager class for handling MongoDB connections and operations.
"""

import logging
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

import pymongo
from pymongo import MongoClient
from src.config import MONGODB_URI, MONGODB_DB

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for MongoDB operations."""
    
    def __init__(self, connection_string: str = MONGODB_URI, db_name: str = MONGODB_DB, test_mode: bool = False):
        """Initialize DatabaseManager with connection string and database name.
        
        Args:
            connection_string: MongoDB connection URI
            db_name: Name of the database to use
            test_mode: If True, skip actual MongoDB connection (for testing)
            
        Raises:
            pymongo.errors.ConnectionFailure: If connection to MongoDB fails
        """
        self.connection_string = connection_string
        self.db_name = db_name
        
        if test_mode:
            # In test mode, we don't actually connect to MongoDB
            logger.info("Initializing DatabaseManager in test mode (no actual connection)")
            self.client = None
            self.db = None
            return
            
        try:
            self.client = MongoClient(connection_string)
            # Force a connection to test it works
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB database: {db_name}")
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise
    
    def get_templates_collection(self):
        """Get the templates collection.
        
        Returns:
            The templates collection
        """
        if self.db is None:
            logger.warning("Attempt to get templates collection in test mode")
            return None
        return self.db["templates"]
    
    def get_filled_forms_collection(self):
        """Get the filled forms collection.
        
        Returns:
            The filled forms collection
        """
        if self.db is None:
            logger.warning("Attempt to get filled forms collection in test mode")
            return None
        return self.db["filled_forms"]
    
    def close_connection(self) -> None:
        """Close the database connection."""
        if self.client is None:
            logger.debug("No connection to close in test mode")
            return
            
        self.client.close()
        logger.info("Closed MongoDB connection")
    
    def ping(self) -> bool:
        """Check if database connection is alive.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.client is None:
            logger.debug("Cannot ping in test mode")
            return False
            
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def create_indexes(self) -> None:
        """Create necessary indexes for collections."""
        if self.db is None:
            logger.warning("Cannot create indexes in test mode")
            return
            
        # Template indexes
        templates_coll = self.get_templates_collection()
        templates_coll.create_index("template_id", unique=True)
        templates_coll.create_index("tags")
        templates_coll.create_index("created_at")
        
        # Filled forms indexes
        forms_coll = self.get_filled_forms_collection()
        forms_coll.create_index("form_id", unique=True)
        forms_coll.create_index("template_id")
        forms_coll.create_index("status")
        forms_coll.create_index("created_at")
        
        logger.info("Created database indexes")
    
    def generate_id(self) -> str:
        """Generate a unique ID.
        
        Returns:
            A unique ID string
        """
        return str(uuid.uuid4())
    
    def get_current_timestamp(self) -> datetime:
        """Get the current timestamp.
        
        Returns:
            Current datetime with timezone info
        """
        return datetime.utcnow() 