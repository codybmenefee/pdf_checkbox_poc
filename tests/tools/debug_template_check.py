#!/usr/bin/env python
"""
Debug script to check templates and forms for potential issues that could
affect field visualization.
"""

import sys
import json
import os
from typing import Dict, Any, List

def check_bbox_format(field: Dict[str, Any]) -> List[str]:
    """Check if the field's bbox has a valid format."""
    issues = []
    if "bbox" not in field:
        issues.append(f"Field '{field.get('name', 'unknown')}' has no bbox")
        return issues
    
    bbox = field.get("bbox", {})
    if not bbox:
        issues.append(f"Field '{field.get('name', 'unknown')}' has empty bbox")
        return issues
    
    # Check if using left/top/right/bottom format
    ltrb_format = all(key in bbox for key in ["left", "top", "right", "bottom"])
    # Check if using left/top/width/height format
    ltwh_format = all(key in bbox for key in ["left", "top", "width", "height"])
    
    if not ltrb_format and not ltwh_format:
        issues.append(f"Field '{field.get('name', 'unknown')}' has invalid bbox format: {bbox}")
    
    # Check for invalid values
    for key, value in bbox.items():
        if not isinstance(value, (int, float)):
            issues.append(f"Field '{field.get('name', 'unknown')}' has non-numeric bbox value for {key}: {value}")
        elif value < 0:
            issues.append(f"Field '{field.get('name', 'unknown')}' has negative bbox value for {key}: {value}")
        elif key in ["left", "top", "right", "bottom", "width", "height"] and value > 1.0:
            issues.append(f"Field '{field.get('name', 'unknown')}' has non-normalized bbox value for {key}: {value}")
    
    # Check if bbox is valid (right > left, bottom > top)
    if ltrb_format:
        if bbox.get("right", 1) <= bbox.get("left", 0):
            issues.append(f"Field '{field.get('name', 'unknown')}' has invalid bbox: right <= left")
        if bbox.get("bottom", 1) <= bbox.get("top", 0):
            issues.append(f"Field '{field.get('name', 'unknown')}' has invalid bbox: bottom <= top")
    
    # Check if width/height are valid
    if ltwh_format:
        if bbox.get("width", 1) <= 0:
            issues.append(f"Field '{field.get('name', 'unknown')}' has invalid bbox: width <= 0")
        if bbox.get("height", 1) <= 0:
            issues.append(f"Field '{field.get('name', 'unknown')}' has invalid bbox: height <= 0")
    
    return issues

def check_template_fields(template_data: Dict[str, Any]) -> List[str]:
    """Check template fields for issues."""
    issues = []
    
    # Check if template has fields
    fields = template_data.get("fields", [])
    if not fields:
        issues.append("Template has no fields")
        return issues
    
    print(f"Checking {len(fields)} fields in template")
    
    # Check each field
    for i, field in enumerate(fields):
        if "name" not in field:
            issues.append(f"Field #{i} has no name")
        
        if "type" not in field:
            issues.append(f"Field '{field.get('name', f'#{i}')}' has no type")
        
        if "page" not in field:
            issues.append(f"Field '{field.get('name', f'#{i}')}' has no page number")
        
        # Check bbox format
        bbox_issues = check_bbox_format(field)
        issues.extend(bbox_issues)
        
        # Check if required fields are present based on type
        field_type = field.get("type", "unknown")
        if field_type == "checkbox" and "value" not in field:
            issues.append(f"Checkbox field '{field.get('name', f'#{i}')}' has no value")
    
    return issues

def check_form_data(form_data: Dict[str, Any]) -> List[str]:
    """Check form data for issues."""
    issues = []
    
    # Check if form has document data
    document_data = form_data.get("document", {})
    if not document_data:
        issues.append("Form has no document data")
    
    # Check if form has template_id
    if "template_id" not in form_data:
        issues.append("Form has no template_id")
    
    # Check if document has stored_filename
    if "stored_filename" not in document_data:
        issues.append("Document has no stored_filename")
    else:
        # Check if the file exists
        stored_filename = document_data.get("stored_filename", "")
        if not os.path.exists(os.path.join("uploads", stored_filename)):
            issues.append(f"Document file not found at uploads/{stored_filename}")
    
    return issues

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_template_check.py <input_json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
        
        # Determine if this is a template or form file
        if "fields" in data:
            print(f"Checking template in {input_file}...")
            issues = check_template_fields(data)
        elif "document" in data:
            print(f"Checking form in {input_file}...")
            issues = check_form_data(data)
        else:
            print(f"Unknown data format in {input_file}")
            sys.exit(1)
        
        if issues:
            print(f"\n⚠️ Found {len(issues)} issues:")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
        else:
            print("✅ No issues found!")
            
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 