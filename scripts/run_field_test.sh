#!/bin/bash

# Run the field visualization test

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Make sure data directory exists
mkdir -p src/data

# Run the field test script
echo "Starting field visualization test..."
python src/run_field_test.py

# Exit with the same exit code as the Python script
exit $?