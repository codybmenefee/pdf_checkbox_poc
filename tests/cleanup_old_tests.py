#!/usr/bin/env python3
"""
Script to clean up test files from original locations after moving them to the new test structure.
"""

import os
import sys
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def remove_original_test_files():
    """Remove test files that have been moved to the new test structure."""
    # Files to remove from root directory
    root_test_files = [
        "test_visualization_feature.py",
        "test_static_paths.py",
        "test_visualization_forms.sh"
    ]
    
    # Check and remove files from root
    for filename in root_test_files:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"✅ Removed {filepath}")
            except Exception as e:
                logger.error(f"❌ Failed to remove {filepath}: {str(e)}")
        else:
            logger.info(f"⚠️ File not found: {filepath}")
    
    # Files that may have been copied from src/
    src_test_files = [
        "test_api.py",
        "test_db.py",
        "test_integration.py",
        "test_utils.py"
    ]
    
    # Check and remove files from src/
    src_dir = os.path.join(BASE_DIR, "src")
    if os.path.exists(src_dir):
        for filename in src_test_files:
            filepath = os.path.join(src_dir, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info(f"✅ Removed {filepath}")
                except Exception as e:
                    logger.error(f"❌ Failed to remove {filepath}: {str(e)}")
            else:
                logger.info(f"⚠️ File not found: {filepath}")
    
    logger.info("Test file cleanup completed!")

def backup_before_cleanup():
    """Create a backup of all test files before removing them."""
    backup_dir = os.path.join(BASE_DIR, "tests", "old_test_backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup files from root
    root_test_files = [
        "test_visualization_feature.py",
        "test_static_paths.py",
        "test_visualization_forms.sh"
    ]
    
    for filename in root_test_files:
        src_path = os.path.join(BASE_DIR, filename)
        if os.path.exists(src_path):
            dest_path = os.path.join(backup_dir, filename)
            try:
                shutil.copy2(src_path, dest_path)
                logger.info(f"✅ Backed up {src_path} to {dest_path}")
            except Exception as e:
                logger.error(f"❌ Failed to backup {src_path}: {str(e)}")
    
    # Backup files from src/
    src_test_files = [
        "test_api.py",
        "test_db.py",
        "test_integration.py",
        "test_utils.py"
    ]
    
    src_dir = os.path.join(BASE_DIR, "src")
    src_backup_dir = os.path.join(backup_dir, "src")
    os.makedirs(src_backup_dir, exist_ok=True)
    
    if os.path.exists(src_dir):
        for filename in src_test_files:
            src_path = os.path.join(src_dir, filename)
            if os.path.exists(src_path):
                dest_path = os.path.join(src_backup_dir, filename)
                try:
                    shutil.copy2(src_path, dest_path)
                    logger.info(f"✅ Backed up {src_path} to {dest_path}")
                except Exception as e:
                    logger.error(f"❌ Failed to backup {src_path}: {str(e)}")
    
    logger.info(f"Test file backup completed! Backups stored in {backup_dir}")

def main():
    """Run the cleanup process."""
    print("This script will remove test files from their original locations.")
    print("Make sure you have verified that all tests work in the new structure before proceeding.")
    
    while True:
        response = input("Do you want to create a backup before removing files? (y/n): ").lower()
        if response in ["y", "yes"]:
            backup_before_cleanup()
            break
        elif response in ["n", "no"]:
            print("Skipping backup...")
            break
        else:
            print("Please enter 'y' or 'n'")
    
    while True:
        response = input("Proceed with removing original test files? (y/n): ").lower()
        if response in ["y", "yes"]:
            remove_original_test_files()
            break
        elif response in ["n", "no"]:
            print("Cleanup cancelled.")
            break
        else:
            print("Please enter 'y' or 'n'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 