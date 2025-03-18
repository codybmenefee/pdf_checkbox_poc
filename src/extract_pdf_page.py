"""
Simple script to extract pages from a PDF as images
for testing the field visualization feature.
"""

import os
import sys
import argparse
from pdf2image import convert_from_path
from PIL import Image

def extract_pdf_pages(pdf_path, output_dir=None, dpi=200, page_numbers=None):
    """
    Extract pages from a PDF file as images.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the images (if None, use same directory as PDF)
        dpi: DPI for rendering (higher means better quality but larger images)
        page_numbers: List of page numbers to extract (1-based index, None means all pages)
    
    Returns:
        List of paths to the generated images
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return []
    
    if output_dir is None:
        output_dir = os.path.dirname(pdf_path) or '.'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi)
        
        # Filter pages if specified
        if page_numbers:
            page_idx = [p-1 for p in page_numbers if 0 < p <= len(images)]
            images = [images[i] for i in page_idx]
        
        # Save images
        output_paths = []
        for i, image in enumerate(images):
            page_num = page_numbers[i] if page_numbers else i + 1
            output_path = os.path.join(output_dir, f"{base_name}_page_{page_num}.png")
            image.save(output_path, 'PNG')
            output_paths.append(output_path)
            print(f"Saved page {page_num} to {output_path}")
        
        return output_paths
    
    except Exception as e:
        print(f"Error extracting PDF pages: {str(e)}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract pages from a PDF as images")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("-o", "--output-dir", help="Directory to save the images")
    parser.add_argument("-d", "--dpi", type=int, default=200, help="DPI for rendering (default: 200)")
    parser.add_argument("-p", "--pages", type=int, nargs="+", help="Page numbers to extract (1-based index)")
    
    args = parser.parse_args()
    
    extract_pdf_pages(args.pdf_path, args.output_dir, args.dpi, args.pages)