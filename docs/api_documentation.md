# PDF Checkbox Extraction & Form Filling System - API Documentation

## Overview

This document provides comprehensive documentation for the PDF Checkbox Extraction & Form Filling System API. The system allows you to extract checkbox fields from PDF documents, store them as templates, and use these templates to fill forms programmatically.

## Base URL

All API endpoints are relative to the base URL of your deployment:

```
http://your-server-address:5000
```

## Authentication

API Key authentication is used for all endpoints. Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

## API Endpoints

### Health Check

#### GET /api/health

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "PDF Checkbox Extraction & Form Filling System is running"
}
```

### Document Management

#### POST /api/documents/upload

Upload a PDF document for processing.

**Request:**
- Content-Type: multipart/form-data
- Body: 
  - file: PDF file to upload

**Response:**
```json
{
  "message": "File uploaded successfully",
  "file_info": {
    "file_id": "f12345",
    "original_filename": "sample.pdf",
    "stored_filename": "f12345_sample.pdf",
    "file_path": "/path/to/file",
    "file_size": 12345
  }
}
```

#### POST /api/documents/{file_id}/process

Process an uploaded PDF document with Google Document AI to extract checkboxes.

**Response:**
```json
{
  "message": "Document processed successfully",
  "file_id": "f12345",
  "checkboxes_count": 5,
  "checkboxes": [
    {
      "label": "Option 1",
      "is_checked": true,
      "page_number": 1,
      "bounding_box": [
        {"x": 100, "y": 200},
        {"x": 120, "y": 200},
        {"x": 120, "y": 220},
        {"x": 100, "y": 220}
      ],
      "normalized_bounding_box": [
        {"x": 0.1, "y": 0.2},
        {"x": 0.12, "y": 0.2},
        {"x": 0.12, "y": 0.22},
        {"x": 0.1, "y": 0.22}
      ],
      "confidence": 0.95
    }
  ]
}
```

### Template Management

#### POST /api/templates

Create a new template from processed document data.

**Request:**
```json
{
  "name": "Sample Template",
  "description": "A sample template for testing",
  "file_id": "f12345",
  "tags": ["sample", "test"]
}
```

**Response:**
```json
{
  "message": "Template created successfully",
  "template_id": "t12345",
  "fields_count": 5
}
```

#### GET /api/templates

List all templates, optionally filtered by tags.

**Query Parameters:**
- tags: Comma-separated list of tags to filter by

**Response:**
```json
{
  "templates": [
    {
      "template_id": "t12345",
      "name": "Sample Template",
      "description": "A sample template for testing",
      "created_at": "2025-03-17T18:00:00Z",
      "updated_at": "2025-03-17T18:00:00Z",
      "tags": ["sample", "test"],
      "version": 1,
      "fields_count": 5
    }
  ]
}
```

#### GET /api/templates/{template_id}

Get a template by ID.

**Response:**
```json
{
  "template": {
    "template_id": "t12345",
    "name": "Sample Template",
    "description": "A sample template for testing",
    "created_at": "2025-03-17T18:00:00Z",
    "updated_at": "2025-03-17T18:00:00Z",
    "tags": ["sample", "test"],
    "version": 1,
    "fields": [
      {
        "field_id": "field_1",
        "field_type": "checkbox",
        "label": "Option 1",
        "page": 1,
        "coordinates": {
          "vertices": [
            {"x": 100, "y": 200},
            {"x": 120, "y": 200},
            {"x": 120, "y": 220},
            {"x": 100, "y": 220}
          ],
          "normalized_vertices": [
            {"x": 0.1, "y": 0.2},
            {"x": 0.12, "y": 0.2},
            {"x": 0.12, "y": 0.22},
            {"x": 0.1, "y": 0.22}
          ]
        },
        "default_value": true,
        "confidence": 0.95
      }
    ]
  }
}
```

### Database Operations

#### POST /api/db/templates

Create a new template in the database.

**Request:**
```json
{
  "name": "Sample Template",
  "description": "A sample template for testing",
  "document_data": {
    "original_filename": "sample.pdf",
    "file_size": 12345,
    "pages": [{"pageNumber": 1}],
    "mime_type": "application/pdf"
  },
  "checkboxes": [
    {
      "label": "Option 1",
      "is_checked": true,
      "page_number": 1,
      "bounding_box": [
        {"x": 100, "y": 200},
        {"x": 120, "y": 200},
        {"x": 120, "y": 220},
        {"x": 100, "y": 220}
      ],
      "normalized_bounding_box": [
        {"x": 0.1, "y": 0.2},
        {"x": 0.12, "y": 0.2},
        {"x": 0.12, "y": 0.22},
        {"x": 0.1, "y": 0.22}
      ],
      "confidence": 0.95
    }
  ],
  "tags": ["sample", "test"]
}
```

**Response:**
```json
{
  "message": "Template created successfully",
  "template_id": "t12345",
  "fields_count": 1
}
```

#### GET /api/db/templates

List templates from the database.

**Query Parameters:**
- tags: Comma-separated list of tags to filter by
- skip: Number of templates to skip (for pagination)
- limit: Maximum number of templates to return (for pagination)

**Response:**
```json
{
  "templates": [
    {
      "template_id": "t12345",
      "name": "Sample Template",
      "description": "A sample template for testing",
      "created_at": "2025-03-17T18:00:00Z",
      "updated_at": "2025-03-17T18:00:00Z",
      "tags": ["sample", "test"],
      "version": 1,
      "fields_count": 1
    }
  ],
  "count": 1,
  "skip": 0,
  "limit": 100
}
```

#### GET /api/db/templates/{template_id}

Get a template from the database.

**Response:**
```json
{
  "template": {
    "template_id": "t12345",
    "name": "Sample Template",
    "description": "A sample template for testing",
    "created_at": "2025-03-17T18:00:00Z",
    "updated_at": "2025-03-17T18:00:00Z",
    "tags": ["sample", "test"],
    "version": 1,
    "fields": [
      {
        "field_id": "field_1",
        "field_type": "checkbox",
        "label": "Option 1",
        "page": 1,
        "coordinates": {
          "vertices": [
            {"x": 100, "y": 200},
            {"x": 120, "y": 200},
            {"x": 120, "y": 220},
            {"x": 100, "y": 220}
          ],
          "normalized_vertices": [
            {"x": 0.1, "y": 0.2},
            {"x": 0.12, "y": 0.2},
            {"x": 0.12, "y": 0.22},
            {"x": 0.1, "y": 0.22}
          ]
        },
        "default_value": true,
        "confidence": 0.95
      }
    ]
  }
}
```

### Form Operations

#### POST /api/forms/fill

Fill a form using a template.

**Request:**
```json
{
  "template_id": "t12345",
  "pdf_file_id": "f12345",
  "name": "Filled Form",
  "field_values": [
    {
      "field_id": "field_1",
      "value": true
    }
  ]
}
```

**Response:**
```json
{
  "message": "Form filled successfully",
  "form_id": "ff12345",
  "filled_pdf_path": "/path/to/filled/pdf"
}
```

#### GET /api/forms/{form_id}/download

Download a filled form.

**Response:**
- Content-Type: application/pdf
- Body: PDF file

#### POST /api/forms/map

Map a template to a document.

**Request:**
```json
{
  "template_id": "t12345",
  "target_document_id": "f67890",
  "source_dimensions": {
    "width": 612,
    "height": 792
  },
  "target_dimensions": {
    "width": 595,
    "height": 842
  }
}
```

**Response:**
```json
{
  "message": "Template mapped to document successfully",
  "mapping": {
    "template_id": "t12345",
    "target_document": {
      "original_filename": "target.pdf",
      "file_size": 12345,
      "page_count": 1
    },
    "field_mappings": [
      {
        "field_id": "field_1",
        "field_type": "checkbox",
        "label": "Option 1",
        "page": 1,
        "source_coordinates": {
          "vertices": [
            {"x": 100, "y": 200},
            {"x": 120, "y": 200},
            {"x": 120, "y": 220},
            {"x": 100, "y": 220}
          ],
          "normalized_vertices": [
            {"x": 0.1, "y": 0.2},
            {"x": 0.12, "y": 0.2},
            {"x": 0.12, "y": 0.22},
            {"x": 0.1, "y": 0.22}
          ]
        },
        "target_coordinates": {
          "vertices": [
            {"x": 97, "y": 213},
            {"x": 117, "y": 213},
            {"x": 117, "y": 233},
            {"x": 97, "y": 233}
          ],
          "normalized_vertices": [
            {"x": 0.1, "y": 0.2},
            {"x": 0.12, "y": 0.2},
            {"x": 0.12, "y": 0.22},
            {"x": 0.1, "y": 0.22}
          ]
        },
        "confidence": 1.0
      }
    ]
  }
}
```

### Validation and Export

#### POST /api/validation/corrections

Apply corrections to a form.

**Request:**
```json
{
  "form_id": "ff12345",
  "corrections": [
    {
      "field_id": "field_1",
      "value": true,
      "position_adjustment": {
        "x": 5,
        "y": -3
      }
    }
  ]
}
```

**Response:**
```json
{
  "message": "Corrections applied successfully",
  "correction_record": {
    "form_id": "ff12345",
    "corrections_applied": 1,
    "timestamp": "2025-03-17T18:18:30Z",
    "status": "success"
  }
}
```

#### GET /api/validation/audit-log

Get the audit log for a form.

**Query Parameters:**
- form_id: ID of the form to get audit log for

**Response:**
```json
{
  "form_id": "ff12345",
  "audit_log": [
    {
      "timestamp": "2025-03-17T18:00:00Z",
      "action": "form_created",
      "user": "system",
      "details": {
        "template_id": "t12345",
        "form_id": "ff12345"
      }
    },
    {
      "timestamp": "2025-03-17T18:05:00Z",
      "action": "field_updated",
      "user": "user@example.com",
      "details": {
        "field_id": "field_1",
        "old_value": false,
        "new_value": true
      }
    }
  ]
}
```

#### POST /api/export/onespan

Export a filled form to OneSpan.

**Request:**
```json
{
  "form_id": "ff12345"
}
```

**Response:**
```json
{
  "message": "Form exported to OneSpan successfully",
  "export_record": {
    "destination": "OneSpan",
    "status": "success",
    "timestamp": "2025-03-17T18:18:30Z",
    "details": {
      "onespan_document_id": "os-ff12345-1234",
      "export_type": "checkbox_form"
    }
  }
}
```

#### POST /api/export/docusign

Export a filled form to DocuSign.

**Request:**
```json
{
  "form_id": "ff12345"
}
```

**Response:**
```json
{
  "message": "Form exported to DocuSign successfully",
  "export_record": {
    "destination": "DocuSign",
    "status": "success",
    "timestamp": "2025-03-17T18:18:30Z",
    "details": {
      "docusign_envelope_id": "ds-ff12345-1234",
      "export_type": "checkbox_form"
    }
  }
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Error responses include a JSON object with an error message:

```json
{
  "error": "Error message describing the issue"
}
```

## Rate Limiting

API requests are rate-limited to 100 requests per minute per API key. Exceeding this limit will result in a 429 Too Many Requests response.

## Webhook Support

The system supports webhooks for asynchronous notifications about form processing and export status. Configure webhooks in the system settings.
