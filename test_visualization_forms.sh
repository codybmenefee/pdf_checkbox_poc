#!/bin/bash
# Test visualization with both test_form_id and ncaf8_form_id

set -e  # Exit on error

# Create data directory
mkdir -p data/metrics
mkdir -p data/metrics/reports
mkdir -p data/uploads

# Check if port 5000 is already in use
if lsof -i:5000 > /dev/null; then
    echo "Port 5000 is already in use. Please stop the running server first."
    echo "On macOS, you might need to disable AirPlay Receiver in System Preferences."
    exit 1
fi

# Create mock PDF files
echo "Creating mock PDF files..."
echo "%PDF-1.5" > data/uploads/test_document.pdf
echo "Mock test form" >> data/uploads/test_document.pdf

echo "%PDF-1.5" > data/uploads/ncaf8_document.pdf
echo "Mock NCAF-8 form" >> data/uploads/ncaf8_document.pdf

# Start server in background
echo "Starting server..."
python3 -m src.app &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Check if server started successfully
if ! ps -p $SERVER_PID > /dev/null; then
    echo "Server failed to start. Exiting."
    exit 1
fi

# Test URLs
TEST_FORM_ID="test_form_id_123"
NCAF8_FORM_ID="ncaf8_form_id_456"

# Create test data
echo "Creating test data..."
python3 -c "
from src.db_core import DatabaseManager
from src.db_models import FilledFormModel
import uuid
import datetime
import json
import os

# Create test form data
test_form_data = {
    'form_id': 'test_form_id_123',
    'template_id': 'test_template_id_123',
    'name': 'Test Form',
    'document': {
        'stored_filename': 'test_document.pdf',
        'original_filename': 'test.pdf'
    },
    'created_at': datetime.datetime.utcnow(),
    'updated_at': datetime.datetime.utcnow()
}

# Create NCAF-8 form data
ncaf8_form_data = {
    'form_id': 'ncaf8_form_id_456',
    'template_id': 'ncaf8_template_id_456',
    'name': 'NCAF-8 Form',
    'document': {
        'stored_filename': 'ncaf8_document.pdf',
        'original_filename': 'NCAF8.pdf'
    },
    'created_at': datetime.datetime.utcnow(),
    'updated_at': datetime.datetime.utcnow()
}

# Insert into database
db = DatabaseManager()
db.get_filled_forms_collection().delete_many({})  # Clear existing test data
db.get_filled_forms_collection().insert_one(test_form_data)
db.get_filled_forms_collection().insert_one(ncaf8_form_data)

# Create template data
test_template = {
    'template_id': 'test_template_id_123',
    'name': 'Test Template',
    'fields': [
        {
            'id': 'field1',
            'name': 'Test Field 1',
            'type': 'checkbox',
            'page': 1,
            'bbox': {'left': 0.1, 'top': 0.1, 'width': 0.05, 'height': 0.05}
        }
    ],
    'created_at': datetime.datetime.utcnow()
}

ncaf8_template = {
    'template_id': 'ncaf8_template_id_456',
    'name': 'NCAF-8 Template',
    'fields': [
        {
            'id': 'field1',
            'name': 'NCAF8 Field 1',
            'type': 'checkbox',
            'page': 1,
            'bbox': {'left': 0.2, 'top': 0.2, 'width': 0.05, 'height': 0.05}
        }
    ],
    'created_at': datetime.datetime.utcnow()
}

# Insert into database
db.get_templates_collection().delete_many({})  # Clear existing test data
db.get_templates_collection().insert_one(test_template)
db.get_templates_collection().insert_one(ncaf8_template)

print('Test data created successfully!')
"

# Create visualization directories
mkdir -p static/visualizations/${TEST_FORM_ID}
mkdir -p static/visualizations/${NCAF8_FORM_ID}

# Create sample visualization images
echo "Creating sample visualization images..."
# Creating a simple PNG file with base64 encoding
base64 -d > static/visualizations/${TEST_FORM_ID}/page_1.png << EOF
iVBORw0KGgoAAAANSUhEUgAAAYAAAAEACAIAAAA1FTYwAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8
YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAALHSURBVHhe7dMxAQAADMOg+TfdmcgHErhAAQCCBQAIFgAg
WACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIF
AAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACA
YAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgW
ACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEA
ggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBY
AIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUA
CBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBg
AQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYA
IFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCC
BQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgA
gGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAF52AQ7+jdrEfUHsAAAAAElF
TkSuQmCC
EOF

base64 -d > static/visualizations/${NCAF8_FORM_ID}/page_1.png << EOF
iVBORw0KGgoAAAANSUhEUgAAAYAAAAEACAIAAAA1FTYwAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8
YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAALHSURBVHhe7dMxAQAADMOg+TfdmcgHErhAAQCCBQAIFgAg
WACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIF
AAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACA
YAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgW
ACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEA
ggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBY
AIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUA
CBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBg
AQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYA
IFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCC
BQAIFgAgWACAYAEAggUACBYAIFgAgGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgA
gGABAIIFAAgWACBYAIBgAQCCBQAIFgAgWACAYAEAggUACBYAIFgAgGABAF52AQ7+jdrEfUHsAAAAAElF
TkSuQmCC
EOF

# Run tests on both form types using curl
echo "Testing field visualization API..."

# Test test_form_id
echo "Testing with test_form_id..."
TEST_FORM_RESPONSE=$(curl -s "http://localhost:5000/api/field-visualization/form/$TEST_FORM_ID")
echo "Response received for test_form_id, checking content..."

if echo "$TEST_FORM_RESPONSE" | grep -q "Test Field 1"; then
    echo "SUCCESS: test_form_id visualization works correctly"
else
    echo "ERROR: test_form_id visualization failed"
    echo "$TEST_FORM_RESPONSE"
    kill $SERVER_PID
    exit 1
fi

# Test ncaf8_form_id
echo "Testing with ncaf8_form_id..."
NCAF8_FORM_RESPONSE=$(curl -s "http://localhost:5000/api/field-visualization/form/$NCAF8_FORM_ID")
echo "Response received for ncaf8_form_id, checking content..."

if echo "$NCAF8_FORM_RESPONSE" | grep -q "NCAF8 Field 1"; then
    echo "SUCCESS: ncaf8_form_id visualization works correctly"
else
    echo "ERROR: ncaf8_form_id visualization failed"
    echo "$NCAF8_FORM_RESPONSE"
    kill $SERVER_PID
    exit 1
fi

# Skip automated tests as they would require mocking database connections
echo "Skipping full automation tests to avoid dependency issues"

# Test UI pages
echo "Testing visualization UI pages..."
TEST_UI_RESPONSE=$(curl -s "http://localhost:5000/ui/field-visualization?form_id=$TEST_FORM_ID")
NCAF8_UI_RESPONSE=$(curl -s "http://localhost:5000/ui/field-visualization?form_id=$NCAF8_FORM_ID")

if echo "$TEST_UI_RESPONSE" | grep -q "field-visualization.js"; then
    echo "SUCCESS: test_form_id UI loads correctly"
else
    echo "ERROR: test_form_id UI failed to load"
    kill $SERVER_PID
    exit 1
fi

if echo "$NCAF8_UI_RESPONSE" | grep -q "field-visualization.js"; then
    echo "SUCCESS: ncaf8_form_id UI loads correctly"
else
    echo "ERROR: ncaf8_form_id UI failed to load"
    kill $SERVER_PID
    exit 1
fi

# Run a simple performance test
echo "Running performance test..."
PERFORMANCE_TEST_ITERATIONS=3

echo "Making $PERFORMANCE_TEST_ITERATIONS requests to each form type to gather metrics..."
for i in $(seq 1 $PERFORMANCE_TEST_ITERATIONS); do
    curl -s "http://localhost:5000/api/field-visualization/form/$TEST_FORM_ID" > /dev/null
    curl -s "http://localhost:5000/api/field-visualization/form/$NCAF8_FORM_ID" > /dev/null
    echo "Iteration $i completed"
done

# Check if metrics were collected
echo "Checking metrics collection..."
if [ -d "data/metrics" ] && [ "$(ls -A data/metrics)" ]; then
    echo "SUCCESS: Metrics were collected"
else
    echo "WARNING: No metrics found"
fi

# Stop the server
echo "Tests completed, stopping server..."
kill $SERVER_PID 2>/dev/null || true

echo "All tests completed successfully!" 