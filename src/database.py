"""
Database models for template storage using MongoDB.
This module provides backward compatibility with the refactored database components.
"""

import logging
from typing import Dict, List, Any, Optional
import datetime
import uuid

# Import refactored components
from src.db_core import DatabaseManager
from src.db_models import TemplateModel, FilledFormModel
from src.db_queries import QueryBuilder, ComplexQueries
from src.db_utils import (
    serialize_mongo_doc, 
    serialize_mongo_docs,
    generate_uuid,
    parse_date_param
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Re-export components for backward compatibility
__all__ = [
    'DatabaseManager',
    'TemplateModel',
    'FilledFormModel'
]
