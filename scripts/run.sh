#!/bin/bash

# PDF Checkbox POC Application Startup Script
# This script sets up the environment and starts the application

# Set default values
PORT=${1:-5004}
LOG_FILE="logs/server.log"

# Set environment variables explicitly
# In production, these should be set in the environment rather than in this script
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    # Fallback default values
    export GCP_PROJECT_ID=onespandemo
    export GCP_LOCATION=us
    export GCP_PROCESSOR_ID=f2a60f0653d61392
    export MONGODB_URI=mongodb://localhost:27017/
    export MONGODB_DB=pdf_checkbox_poc
    echo "Warning: No .env file found. Using default environment variables."
fi

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
    
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run pre-flight checks
echo "Running pre-flight checks..."
if ! python3 -c "import pymongo; import reportlab; import google.cloud; import flask;" 2>/dev/null; then
    echo "Error: Missing required Python packages. Make sure requirements.txt is installed correctly."
    exit 1
fi

# Clear previous log
echo "Application started at $(date)" > $LOG_FILE

# Run the application
echo "Starting application on port $PORT..."
echo "Logs will be written to $LOG_FILE"
python -m src.app --port=$PORT 2>&1 | tee -a $LOG_FILE 