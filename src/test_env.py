"""
Test script to verify environment variables are loaded correctly.
"""

import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
logger.debug("Loading environment variables...")
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
logger.debug(f"Looking for .env file at: {env_path}")
logger.debug(f"File exists: {os.path.exists(env_path)}")
load_dotenv(env_path, override=True)

# Print environment variables
logger.debug("Environment variables:")
logger.debug(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")
logger.debug(f"GCP_LOCATION: {os.environ.get('GCP_LOCATION')}")
logger.debug(f"GCP_PROCESSOR_ID: {os.environ.get('GCP_PROCESSOR_ID')}")

if __name__ == "__main__":
    print("Test complete. Check the logs above for environment variable values.") 