"""
API endpoints for the database models.
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional

from src.db_core import DatabaseManager
from src.db_models import TemplateModel, FilledFormModel
from src.db_queries import QueryBuilder, ComplexQueries
from src.db_utils import (
    serialize_mongo_doc, 
    serialize_mongo_docs,
    parse_date_param,
    format_query_results,
    paginate_results,
    extract_query_params
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
db_api = Blueprint('db_api', __name__)

# Initialize models
db_manager = DatabaseManager()
template_model = TemplateModel(db_manager)
filled_form_model = FilledFormModel(db_manager)
complex_queries = ComplexQueries(db_manager)

@db_api.route('/api/db/templates', methods=['POST'])
def create_template():
    """Create a new template in the database."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate required fields
    required_fields = ['name', 'description', 'document_data', 'checkboxes']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Create template
    template = template_model.create(
        name=data['name'],
        description=data['description'],
        document_data=data['document_data'],
        checkboxes=data['checkboxes'],
        tags=data.get('tags', [])
    )
    
    if not template:
        return jsonify({"error": "Failed to create template"}), 500
    
    return jsonify(serialize_mongo_doc(template)), 201


@db_api.route('/api/db/templates', methods=['GET'])
def list_templates():
    """List templates from the database."""
    try:
        # Get query parameters
        tags = request.args.getlist('tag')
        search = request.args.get('search')
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 100))
        created_after = parse_date_param(request.args.get('created_after'))
        created_before = parse_date_param(request.args.get('created_before'))
        
        # Check if we need complex query
        if search or created_after or created_before:
            # Build query filter
            query_filter = QueryBuilder.build_template_filter(
                tags=tags,
                name_contains=search,
                created_after=created_after,
                created_before=created_before
            )
            
            # Execute search
            templates = list(db_manager.get_templates_collection().find(query_filter).skip(skip).limit(limit))
        else:
            # Use simple list
            templates = template_model.list(tags=tags, skip=skip, limit=limit)
        
        # Format response
        response = {
            "templates": serialize_mongo_docs(templates),
            "count": len(templates),
            "skip": skip,
            "limit": limit
        }
        
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return jsonify({"error": "Failed to list templates"}), 500


@db_api.route('/api/db/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a template by ID."""
    try:
        # Check if we need to include filled forms
        include_forms = request.args.get('include_forms', '').lower() == 'true'
        
        if include_forms:
            result = complex_queries.get_template_with_filled_forms(template_id)
            if not result:
                return jsonify({"error": "Template not found"}), 404
                
            return jsonify(serialize_mongo_doc(result)), 200
        else:
            template = template_model.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404
                
            return jsonify(serialize_mongo_doc(template)), 200
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        return jsonify({"error": "Failed to get template"}), 500


@db_api.route('/api/db/templates/<template_id>', methods=['PUT'])
def update_template(template_id):
    """Update a template."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        # Update template
        updated_template = template_model.update(template_id, data)
        
        if not updated_template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify(serialize_mongo_doc(updated_template)), 200
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        return jsonify({"error": "Failed to update template"}), 500


@db_api.route('/api/db/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template."""
    try:
        success = template_model.delete(template_id)
        
        if not success:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({"message": "Template deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        return jsonify({"error": "Failed to delete template"}), 500


@db_api.route('/api/db/templates/<template_id>/tags', methods=['POST'])
def add_tag(template_id):
    """Add a tag to a template."""
    data = request.json
    
    if not data or 'tag' not in data:
        return jsonify({"error": "No tag provided"}), 400
    
    tag = data['tag']
    
    try:
        success = template_model.add_tag(template_id, tag)
        
        if not success:
            return jsonify({"error": "Template not found or tag already exists"}), 404
        
        # Get updated template
        template = template_model.get(template_id)
        
        return jsonify(serialize_mongo_doc(template)), 200
    except Exception as e:
        logger.error(f"Error adding tag to template {template_id}: {e}")
        return jsonify({"error": "Failed to add tag"}), 500


@db_api.route('/api/db/templates/<template_id>/tags/<tag>', methods=['DELETE'])
def remove_tag(template_id, tag):
    """Remove a tag from a template."""
    try:
        success = template_model.remove_tag(template_id, tag)
        
        if not success:
            return jsonify({"error": "Template not found or tag not found"}), 404
        
        # Get updated template
        template = template_model.get(template_id)
        
        return jsonify(serialize_mongo_doc(template)), 200
    except Exception as e:
        logger.error(f"Error removing tag from template {template_id}: {e}")
        return jsonify({"error": "Failed to remove tag"}), 500


@db_api.route('/api/db/forms', methods=['POST'])
def create_filled_form():
    """Create a new filled form."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate required fields
    required_fields = ['template_id', 'name', 'document_info', 'field_values']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Create filled form
    form = filled_form_model.create(
        template_id=data['template_id'],
        name=data['name'],
        document_info=data['document_info'],
        field_values=data['field_values']
    )
    
    if not form:
        return jsonify({"error": "Failed to create filled form"}), 500
    
    return jsonify(serialize_mongo_doc(form)), 201


@db_api.route('/api/db/forms', methods=['GET'])
def list_filled_forms():
    """List filled forms from the database."""
    try:
        # Get query parameters
        template_id = request.args.get('template_id')
        status = request.args.get('status')
        search = request.args.get('search')
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 100))
        created_after = parse_date_param(request.args.get('created_after'))
        created_before = parse_date_param(request.args.get('created_before'))
        
        # Check if we need complex query
        if search or created_after or created_before:
            # Build query filter
            query_filter = QueryBuilder.build_form_filter(
                template_id=template_id,
                status=status,
                name_contains=search,
                created_after=created_after,
                created_before=created_before
            )
            
            # Execute search
            forms = list(db_manager.get_filled_forms_collection().find(query_filter).skip(skip).limit(limit))
        else:
            # Use simple list
            forms = filled_form_model.list(template_id=template_id, status=status, skip=skip, limit=limit)
        
        # Format response
        response = {
            "forms": serialize_mongo_docs(forms),
            "count": len(forms),
            "skip": skip,
            "limit": limit
        }
        
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error listing filled forms: {e}")
        return jsonify({"error": "Failed to list filled forms"}), 500


@db_api.route('/api/db/forms/<form_id>', methods=['GET'])
def get_filled_form(form_id):
    """Get a filled form by ID."""
    try:
        form = filled_form_model.get(form_id)
        
        if not form:
            return jsonify({"error": "Filled form not found"}), 404
            
        return jsonify(serialize_mongo_doc(form)), 200
    except Exception as e:
        logger.error(f"Error getting filled form {form_id}: {e}")
        return jsonify({"error": "Failed to get filled form"}), 500


@db_api.route('/api/db/forms/<form_id>/fields', methods=['PUT'])
def update_field_values(form_id):
    """Update field values for a filled form."""
    data = request.json
    
    if not data or 'field_values' not in data:
        return jsonify({"error": "No field values provided"}), 400
    
    try:
        updated_form = filled_form_model.update_field_values(form_id, data['field_values'])
        
        if not updated_form:
            return jsonify({"error": "Filled form not found"}), 404
        
        return jsonify(serialize_mongo_doc(updated_form)), 200
    except Exception as e:
        logger.error(f"Error updating field values for form {form_id}: {e}")
        return jsonify({"error": "Failed to update field values"}), 500


@db_api.route('/api/db/forms/<form_id>/status', methods=['PUT'])
def update_form_status(form_id):
    """Update status for a filled form."""
    data = request.json
    
    if not data or 'status' not in data:
        return jsonify({"error": "No status provided"}), 400
    
    try:
        updated_form = filled_form_model.update_status(form_id, data['status'])
        
        if not updated_form:
            return jsonify({"error": "Filled form not found"}), 404
        
        return jsonify(serialize_mongo_doc(updated_form)), 200
    except Exception as e:
        logger.error(f"Error updating status for form {form_id}: {e}")
        return jsonify({"error": "Failed to update status"}), 500


@db_api.route('/api/db/forms/<form_id>/export', methods=['POST'])
def add_export_record(form_id):
    """Add an export record to a filled form."""
    data = request.json
    
    if not data or 'destination' not in data or 'status' not in data:
        return jsonify({"error": "Missing required fields: destination, status"}), 400
    
    try:
        updated_form = filled_form_model.add_export_record(
            form_id, 
            data['destination'], 
            data['status']
        )
        
        if not updated_form:
            return jsonify({"error": "Filled form not found"}), 404
        
        return jsonify(serialize_mongo_doc(updated_form)), 200
    except Exception as e:
        logger.error(f"Error adding export record for form {form_id}: {e}")
        return jsonify({"error": "Failed to add export record"}), 500


@db_api.route('/api/db/forms/<form_id>', methods=['DELETE'])
def delete_filled_form(form_id):
    """Delete a filled form."""
    try:
        success = filled_form_model.delete(form_id)
        
        if not success:
            return jsonify({"error": "Filled form not found"}), 404
        
        return jsonify({"message": "Filled form deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting filled form {form_id}: {e}")
        return jsonify({"error": "Failed to delete filled form"}), 500


@db_api.route('/api/db/stats/forms', methods=['GET'])
def get_form_stats():
    """Get statistics about filled forms."""
    try:
        template_id = request.args.get('template_id')
        
        stats = complex_queries.get_form_statistics(template_id)
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting form statistics: {e}")
        return jsonify({"error": "Failed to get form statistics"}), 500


@db_api.route('/api/db/search/templates', methods=['GET'])
def search_templates():
    """Search templates by name or tags."""
    try:
        search_term = request.args.get('q')
        tags = request.args.getlist('tag')
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 100))
        
        templates = complex_queries.search_templates(search_term, tags, skip, limit)
        
        response = {
            "templates": serialize_mongo_docs(templates),
            "count": len(templates),
            "query": {
                "search_term": search_term,
                "tags": tags
            }
        }
        
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error searching templates: {e}")
        return jsonify({"error": "Failed to search templates"}), 500
