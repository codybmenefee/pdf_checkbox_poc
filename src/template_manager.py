"""
Template model for storing extracted checkbox data.
"""

from typing import Dict, List, Any, Optional
import datetime
import uuid
import json
import os
import logging

from src.config import TEMPLATE_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateManager:
    """Manager for template storage and retrieval."""
    
    def __init__(self):
        """Initialize the template manager."""
        # Ensure template directory exists
        os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
        logger.info(f"Initialized Template Manager with template folder: {TEMPLATE_FOLDER}")
    
    def create_template(self, name: str, description: str, document_data: Dict[str, Any], 
                        fields: List[Dict[str, Any]], tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new template from extracted form field data.
        
        Args:
            name: Template name
            description: Template description
            document_data: Document data from Document AI
            fields: List of extracted form fields
            tags: Optional list of tags
            
        Returns:
            Dictionary with template information
        """
        # Generate a unique ID for the template
        template_id = str(uuid.uuid4())
        
        # Create template metadata
        template = {
            "template_id": template_id,
            "name": name,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "tags": tags or [],
            "version": 1,
            "document": {
                "original_filename": document_data.get("original_filename", ""),
                "file_size": document_data.get("file_size", 0),
                "page_count": len(document_data.get("pages", [])),
                "mime_type": document_data.get("mime_type", "application/pdf")
            },
            "fields": []
        }
        
        # Add form fields
        for i, field in enumerate(fields):
            field_id = f"field_{i+1}"
            field_data = {
                "field_id": field_id,
                "field_type": field.get("field_type", "text"),
                "label": field.get("label", f"Field {i+1}"),
                "page": field.get("page_number", 1),
                "coordinates": {
                    "vertices": field.get("bounding_box", []),
                    "normalized_vertices": field.get("normalized_bounding_box", [])
                },
                "default_value": field.get("is_checked", False) if field.get("field_type") == "checkbox" else field.get("value", ""),
                "confidence": field.get("confidence", 0)
            }
            template["fields"].append(field_data)
        
        # Save the template to a file
        template_filename = f"{template_id}.json"
        template_path = os.path.join(TEMPLATE_FOLDER, template_filename)
        
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Created template: {template_path}")
        
        return template
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template dictionary or None if not found
        """
        template_path = os.path.join(TEMPLATE_FOLDER, f"{template_id}.json")
        
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_id}")
            return None
        
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        return template
    
    def list_templates(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all templates, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by
            
        Returns:
            List of template dictionaries
        """
        templates = []
        
        for filename in os.listdir(TEMPLATE_FOLDER):
            if filename.endswith('.json'):
                template_path = os.path.join(TEMPLATE_FOLDER, filename)
                
                with open(template_path, 'r') as f:
                    template = json.load(f)
                
                # Filter by tags if specified
                if tags:
                    if not all(tag in template.get("tags", []) for tag in tags):
                        continue
                
                templates.append(template)
        
        return templates
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a template.
        
        Args:
            template_id: Template ID
            updates: Dictionary with updates
            
        Returns:
            Updated template dictionary or None if not found
        """
        template = self.get_template(template_id)
        
        if not template:
            return None
        
        # Update template fields
        for key, value in updates.items():
            if key != "template_id" and key != "created_at":
                template[key] = value
        
        # Update the updated_at timestamp
        template["updated_at"] = datetime.datetime.now().isoformat()
        
        # Increment version
        template["version"] += 1
        
        # Save the updated template
        template_path = os.path.join(TEMPLATE_FOLDER, f"{template_id}.json")
        
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Updated template: {template_path}")
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False if not found
        """
        template_path = os.path.join(TEMPLATE_FOLDER, f"{template_id}.json")
        
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_id}")
            return False
        
        os.remove(template_path)
        logger.info(f"Deleted template: {template_path}")
        
        return True
