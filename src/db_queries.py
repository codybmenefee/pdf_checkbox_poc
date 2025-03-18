"""
Query building and complex database queries for the PDF Checkbox POC project.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import pymongo
from bson import ObjectId

from src.db_core import DatabaseManager
from src.db_models import TemplateModel, FilledFormModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryBuilder:
    """Utility class for building MongoDB queries."""
    
    @staticmethod
    def build_template_filter(
        tags: Optional[List[str]] = None,
        name_contains: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Build a filter for template queries.
        
        Args:
            tags: Filter by tags (all must match)
            name_contains: Filter by name containing this string
            created_after: Filter templates created after this date
            created_before: Filter templates created before this date
            
        Returns:
            A query filter dictionary
        """
        filter_query = {}
        
        if tags:
            filter_query["tags"] = {"$all": tags}
        
        if name_contains:
            filter_query["name"] = {"$regex": name_contains, "$options": "i"}
        
        # Handle date range
        if created_after or created_before:
            filter_query["created_at"] = {}
            
            if created_after:
                filter_query["created_at"]["$gte"] = created_after
                
            if created_before:
                filter_query["created_at"]["$lte"] = created_before
        
        return filter_query
    
    @staticmethod
    def build_form_filter(
        template_id: Optional[str] = None,
        status: Optional[str] = None,
        name_contains: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Build a filter for form queries.
        
        Args:
            template_id: Filter by template ID
            status: Filter by status
            name_contains: Filter by name containing this string
            created_after: Filter forms created after this date
            created_before: Filter forms created before this date
            
        Returns:
            A query filter dictionary
        """
        filter_query = {}
        
        if template_id:
            filter_query["template_id"] = template_id
        
        if status:
            filter_query["status"] = status
        
        if name_contains:
            filter_query["name"] = {"$regex": name_contains, "$options": "i"}
        
        # Handle date range
        if created_after or created_before:
            filter_query["created_at"] = {}
            
            if created_after:
                filter_query["created_at"]["$gte"] = created_after
                
            if created_before:
                filter_query["created_at"]["$lte"] = created_before
        
        return filter_query


class ComplexQueries:
    """Handles complex queries that involve multiple collections or aggregations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with a database manager.
        
        Args:
            db_manager: The database manager instance
        """
        self.db_manager = db_manager
        self.templates_collection = db_manager.get_templates_collection()
        self.forms_collection = db_manager.get_filled_forms_collection()
        self.template_model = TemplateModel(db_manager)
        self.form_model = FilledFormModel(db_manager)
    
    def get_template_with_filled_forms(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template with all its filled forms.
        
        Args:
            template_id: The template ID
            
        Returns:
            Dictionary with template and filled_forms, or None if template not found
        """
        # Get the template first
        template = self.template_model.get(template_id)
        if not template:
            return None
        
        # Get all forms for this template
        forms = self.form_model.list(template_id=template_id)
        
        # Return combined result
        return {
            "template": template,
            "filled_forms": forms
        }
    
    def search_templates(
        self,
        search_term: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search templates by name and/or tags.
        
        Args:
            search_term: Search term to match in name or description
            tags: List of tags to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return
            
        Returns:
            List of matching templates
        """
        # Build query
        query = {}
        
        if search_term:
            query["name"] = {"$regex": search_term, "$options": "i"}
            
        if tags:
            query["tags"] = {"$all": tags}
        
        # Execute search
        results = self.templates_collection.find(query).skip(skip).limit(limit)
        
        return list(results)
    
    def get_form_statistics(self, template_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about forms.
        
        Args:
            template_id: Optional template ID to filter by
            
        Returns:
            Dictionary with statistics
        """
        # Build match stage
        match_stage = {}
        if template_id:
            match_stage["template_id"] = template_id
        
        # Build aggregation pipeline
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        # Execute aggregation
        results = list(self.forms_collection.aggregate(pipeline))
        
        # Format results
        stats = {
            "total": sum(item["count"] for item in results),
            "by_status": {item["_id"]: item["count"] for item in results}
        }
        
        return stats
    
    def get_templates_with_form_counts(
        self, skip: int = 0, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get templates with counts of associated forms.
        
        Args:
            skip: Number of results to skip
            limit: Maximum number of results to return
            
        Returns:
            List of templates with form counts
        """
        # Get templates first
        templates = self.template_model.list(skip=skip, limit=limit)
        
        # For each template, get the count of forms
        for template in templates:
            template_id = template["template_id"]
            
            # Using aggregation to get count
            pipeline = [
                {"$match": {"template_id": template_id}},
                {"$group": {"_id": "$template_id", "count": {"$sum": 1}}}
            ]
            
            results = list(self.forms_collection.aggregate(pipeline))
            form_count = results[0]["count"] if results else 0
            
            # Add count to template
            template["form_count"] = form_count
        
        return templates
    
    def find_forms_with_field_value(
        self,
        field_key: str,
        field_value: Any,
        template_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find forms that have a specific field value.
        
        Args:
            field_key: The field key to match
            field_value: The field value to match
            template_id: Optional template ID to filter by
            
        Returns:
            List of matching forms
        """
        # Build query
        query = {
            "field_values": {
                "$elemMatch": {
                    "key": field_key,
                    "value": field_value
                }
            }
        }
        
        if template_id:
            query["template_id"] = template_id
        
        # Execute query
        results = self.forms_collection.find(query)
        
        return list(results) 