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

# Run Flask (using port 5001 to avoid conflicts)
python3 -m flask --app src.app run --debug --port=5001 