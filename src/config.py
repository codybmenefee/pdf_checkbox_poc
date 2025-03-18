"""
Configuration settings for the PDF Checkbox Extraction & Form Filling System.
"""

import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
logger.debug("Loading environment variables...")
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
logger.debug(f"Looking for .env file at: {env_path}")
logger.debug(f"File exists: {os.path.exists(env_path)}")

# Load environment variables
load_dotenv(env_path, override=True)

# Google Cloud settings
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us")  # Format is 'us' or 'eu'
GCP_PROCESSOR_ID = os.environ.get("GCP_PROCESSOR_ID")

# Validate required settings
if not GCP_PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID is not set in environment variables")
if not GCP_PROCESSOR_ID:
    raise ValueError("GCP_PROCESSOR_ID is not set in environment variables")

logger.debug(f"Loaded GCP settings:")
logger.debug(f"GCP_PROJECT_ID: {GCP_PROJECT_ID}")
logger.debug(f"GCP_LOCATION: {GCP_LOCATION}")
logger.debug(f"GCP_PROCESSOR_ID: {GCP_PROCESSOR_ID}")

# MongoDB settings
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.environ.get("MONGODB_DB", "pdf_checkbox_poc")

# Application settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
PROCESSED_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "templates")
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
