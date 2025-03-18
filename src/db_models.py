"""
Data models and schema definitions for the database.
"""

import logging
from typing import Dict, List, Any, Optional
import datetime
import uuid

from src.db_core import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateModel:
    """Model for template operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the template model.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_templates_collection()
    
    def create(self, name: str, description: str, document_data: Dict[str, Any], 
               checkboxes: List[Dict[str, Any]], tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new template.
        
        Args:
            name: Template name
            description: Template description
            document_data: Document metadata
            checkboxes: List of checkbox definitions
            tags: Optional list of tags
            
        Returns:
            Dict containing the created template
        """
        template_id = str(uuid.uuid4())
        created_at = self.db_manager.get_current_timestamp()
        
        template = {
            "template_id": template_id,
            "name": name,
            "description": description,
            "document_data": document_data,
            "checkboxes": checkboxes,
            "tags": tags or [],
            "created_at": created_at,
            "updated_at": created_at
        }
        
        try:
            result = self.collection.insert_one(template)
            if result.acknowledged:
                logger.info(f"Created template: {template_id}")
                return template
            else:
                logger.error("Failed to create template")
                return None
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return None
    
    def get(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template dict or None if not found
        """
        try:
            template = self.collection.find_one({"template_id": template_id})
            if template:
                logger.info(f"Retrieved template: {template_id}")
                return template
            else:
                logger.warning(f"Template not found: {template_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving template: {e}")
            return None
    
    def list(self, tags: Optional[List[str]] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List templates, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of template dicts
        """
        query = {}
        if tags and len(tags) > 0:
            query = {"tags": {"$all": tags}}
        
        try:
            templates = list(self.collection.find(query).skip(skip).limit(limit))
            logger.info(f"Listed {len(templates)} templates")
            return templates
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def update(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a template.
        
        Args:
            template_id: Template ID
            updates: Dict of fields to update
            
        Returns:
            Updated template dict or None if failed
        """
        try:
            # Check if template exists
            template = self.collection.find_one({"template_id": template_id})
            if not template:
                logger.warning(f"Template not found for update: {template_id}")
                return None
            
            # Prepare update
            updates["updated_at"] = self.db_manager.get_current_timestamp()
            
            # Remove fields that shouldn't be updated directly
            if "template_id" in updates:
                del updates["template_id"]
            if "created_at" in updates:
                del updates["created_at"]
            
            # Update the document
            result = self.collection.update_one(
                {"template_id": template_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated template: {template_id}")
                return self.get(template_id)
            else:
                logger.warning(f"No changes made to template: {template_id}")
                return template
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return None
    
    def delete(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({"template_id": template_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted template: {template_id}")
                return True
            else:
                logger.warning(f"Template not found for deletion: {template_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    def add_tag(self, template_id: str, tag: str) -> bool:
        """
        Add a tag to a template.
        
        Args:
            template_id: Template ID
            tag: Tag to add
            
        Returns:
            True if added, False otherwise
        """
        try:
            # Check if template exists
            template = self.collection.find_one({"template_id": template_id})
            if not template:
                logger.warning(f"Template not found for adding tag: {template_id}")
                return False
            
            # Add tag if not already present
            if tag in template.get("tags", []):
                logger.info(f"Tag already exists on template: {tag}")
                return True
            
            # Update the document
            result = self.collection.update_one(
                {"template_id": template_id},
                {
                    "$push": {"tags": tag},
                    "$set": {"updated_at": self.db_manager.get_current_timestamp()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Added tag to template: {tag}")
                return True
            else:
                logger.warning(f"Failed to add tag: {tag}")
                return False
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            return False
    
    def remove_tag(self, template_id: str, tag: str) -> bool:
        """
        Remove a tag from a template.
        
        Args:
            template_id: Template ID
            tag: Tag to remove
            
        Returns:
            True if removed, False otherwise
        """
        try:
            # Check if template exists
            template = self.collection.find_one({"template_id": template_id})
            if not template:
                logger.warning(f"Template not found for removing tag: {template_id}")
                return False
            
            # Remove tag
            result = self.collection.update_one(
                {"template_id": template_id},
                {
                    "$pull": {"tags": tag},
                    "$set": {"updated_at": self.db_manager.get_current_timestamp()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Removed tag from template: {tag}")
                return True
            else:
                logger.warning(f"Tag not found or failed to remove: {tag}")
                return False
        except Exception as e:
            logger.error(f"Error removing tag: {e}")
            return False


class FilledFormModel:
    """Model for filled form operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the filled form model.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_filled_forms_collection()
    
    def create(self, template_id: str, name: str, document_info: Dict[str, Any], 
               field_values: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a new filled form.
        
        Args:
            template_id: Template ID
            name: Form name
            document_info: Document metadata
            field_values: List of field values
            
        Returns:
            Dict containing the created form
        """
        form_id = str(uuid.uuid4())
        created_at = self.db_manager.get_current_timestamp()
        
        form = {
            "form_id": form_id,
            "template_id": template_id,
            "name": name,
            "document_info": document_info,
            "field_values": field_values,
            "status": "draft",
            "exports": [],
            "created_at": created_at,
            "updated_at": created_at
        }
        
        try:
            result = self.collection.insert_one(form)
            if result.acknowledged:
                logger.info(f"Created filled form: {form_id}")
                return form
            else:
                logger.error("Failed to create filled form")
                return None
        except Exception as e:
            logger.error(f"Error creating filled form: {e}")
            return None
    
    def get(self, form_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a filled form by ID.
        
        Args:
            form_id: Form ID
            
        Returns:
            Form dict or None if not found
        """
        try:
            form = self.collection.find_one({"form_id": form_id})
            if form:
                logger.info(f"Retrieved filled form: {form_id}")
                return form
            else:
                logger.warning(f"Filled form not found: {form_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving filled form: {e}")
            return None
    
    def list(self, template_id: Optional[str] = None, status: Optional[str] = None, 
             skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List filled forms, optionally filtered by template ID and status.
        
        Args:
            template_id: Optional template ID to filter by
            status: Optional status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of form dicts
        """
        query = {}
        if template_id:
            query["template_id"] = template_id
        if status:
            query["status"] = status
        
        try:
            forms = list(self.collection.find(query).skip(skip).limit(limit))
            logger.info(f"Listed {len(forms)} filled forms")
            return forms
        except Exception as e:
            logger.error(f"Error listing filled forms: {e}")
            return []
    
    def update_field_values(self, form_id: str, field_values: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Update field values for a filled form.
        
        Args:
            form_id: Form ID
            field_values: List of field values
            
        Returns:
            Updated form dict or None if failed
        """
        try:
            # Check if form exists
            form = self.collection.find_one({"form_id": form_id})
            if not form:
                logger.warning(f"Filled form not found for update: {form_id}")
                return None
            
            # Update the document
            result = self.collection.update_one(
                {"form_id": form_id},
                {
                    "$set": {
                        "field_values": field_values,
                        "updated_at": self.db_manager.get_current_timestamp()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated field values for form: {form_id}")
                return self.get(form_id)
            else:
                logger.warning(f"No changes made to field values: {form_id}")
                return form
        except Exception as e:
            logger.error(f"Error updating field values: {e}")
            return None
    
    def update_status(self, form_id: str, status: str) -> Optional[Dict[str, Any]]:
        """
        Update status for a filled form.
        
        Args:
            form_id: Form ID
            status: New status
            
        Returns:
            Updated form dict or None if failed
        """
        try:
            # Check if form exists
            form = self.collection.find_one({"form_id": form_id})
            if not form:
                logger.warning(f"Filled form not found for status update: {form_id}")
                return None
            
            # Update the document
            result = self.collection.update_one(
                {"form_id": form_id},
                {
                    "$set": {
                        "status": status,
                        "updated_at": self.db_manager.get_current_timestamp()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated status for form: {form_id} to {status}")
                return self.get(form_id)
            else:
                logger.warning(f"No changes made to status: {form_id}")
                return form
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            return None
    
    def add_export_record(self, form_id: str, destination: str, status: str) -> Optional[Dict[str, Any]]:
        """
        Add an export record to a filled form.
        
        Args:
            form_id: Form ID
            destination: Export destination
            status: Export status
            
        Returns:
            Updated form dict or None if failed
        """
        try:
            # Check if form exists
            form = self.collection.find_one({"form_id": form_id})
            if not form:
                logger.warning(f"Filled form not found for adding export: {form_id}")
                return None
            
            # Create export record
            export_record = {
                "destination": destination,
                "status": status,
                "timestamp": self.db_manager.get_current_timestamp()
            }
            
            # Update the document
            result = self.collection.update_one(
                {"form_id": form_id},
                {
                    "$push": {"exports": export_record},
                    "$set": {"updated_at": self.db_manager.get_current_timestamp()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Added export record to form: {form_id}")
                return self.get(form_id)
            else:
                logger.warning(f"Failed to add export record: {form_id}")
                return form
        except Exception as e:
            logger.error(f"Error adding export record: {e}")
            return None
    
    def delete(self, form_id: str) -> bool:
        """
        Delete a filled form.
        
        Args:
            form_id: Form ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({"form_id": form_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted filled form: {form_id}")
                return True
            else:
                logger.warning(f"Filled form not found for deletion: {form_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting filled form: {e}")
            return False 