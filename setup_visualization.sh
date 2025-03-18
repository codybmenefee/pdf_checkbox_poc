#!/bin/bash

# Setup script for PDF field visualization feature
# This script sets up and tests the PDF field visualization feature

set -e  # Exit on error

echo "=== PDF Field Visualization Setup ==="
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data/templates
mkdir -p data/test_pdfs
mkdir -p static/images
mkdir -p static/visualizations
echo "Directories created."
echo ""

# Generate placeholder images
echo "Generating placeholder images..."
python3 generate_placeholders.py
echo ""

# Generate test PDF
echo "Generating test PDF..."
python3 generate_test_pdf.py
echo ""

# Run test script
echo "Running test script to verify setup..."
python3 test_visualization_feature.py
echo ""

echo "=== Setup Complete ==="
echo ""
echo "You can now access the visualization feature at:"
echo "http://localhost:5000/ui/template-advanced-visualization/test-visualization-template"
echo ""
echo "Make sure your server is running with: ./run.sh"
echo "" 