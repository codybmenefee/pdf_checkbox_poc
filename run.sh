#!/bin/bash

# Set environment variables explicitly
export GCP_PROJECT_ID=onespandemo
export GCP_LOCATION=us
export GCP_PROCESSOR_ID=f2a60f0653d61392
export MONGODB_URI=mongodb://localhost:27017/
export MONGODB_DB=pdf_checkbox_poc

# We can use one of two approaches:
# 1. Set PYTHONPATH to include the current directory (this allows imports like 'from src.config import...')
# 2. Add the src directory to Python path (this allows imports like 'from config import...')
# Let's use approach #1 which is more standard

# Set Python path to include the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check for Python virtual environment
if [ -d "venv" ]; then
    echo "Using existing virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Run the application with a different port
echo "Starting application..."
python -m src.app --port=5004

# Keep log of application
echo "Application started!" > server.log 