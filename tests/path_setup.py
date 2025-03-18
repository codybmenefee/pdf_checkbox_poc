"""
Module to set up system path for importing project modules.
This should be imported by test files that need to import from the main project.
"""
import os
import sys

# Add the project root directory to the path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Add tests directory to the path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

# Add the src directory to the path
SRC_DIR = os.path.join(BASE_DIR, 'src')
if os.path.exists(SRC_DIR) and SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR) 