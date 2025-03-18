"""
Document AI module for PDF checkbox extraction.
"""

from document_ai.document_ai_core import DocumentAIManager
from document_ai.document_ai_models import DocumentModel
from document_ai.document_ai_utils import (
    normalize_bounding_box,
    save_document_as_json,
    get_confidence_score,
    encode_image_for_visualization,
    generate_color_for_field,
    generate_visualization_data
)

__all__ = [
    'DocumentAIManager',
    'DocumentModel',
    'normalize_bounding_box',
    'save_document_as_json',
    'get_confidence_score',
    'encode_image_for_visualization',
    'generate_color_for_field',
    'generate_visualization_data'
] 