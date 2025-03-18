"""
Tests for static file handling functionality.
"""

import os
import tempfile
import shutil
import unittest
from flask import Flask

from src.app import app
import src.app as app_module


class TestStaticFileHandling(unittest.TestCase):
    """Test static file handling functionality."""

    def setUp(self):
        """Set up test environment."""
        # Configure Flask for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temporary test directories and files
        self.test_dir = tempfile.mkdtemp()
        self.static_dir = os.path.join(self.test_dir, 'static')
        self.vis_dir = os.path.join(self.static_dir, 'visualizations')
        self.test_id = 'test-visualization-id'
        self.test_vis_dir = os.path.join(self.vis_dir, self.test_id)
        
        # Create directory structure
        os.makedirs(self.test_vis_dir, exist_ok=True)
        
        # Create test files
        self.test_file = os.path.join(self.test_vis_dir, 'test_page.png')
        with open(self.test_file, 'wb') as f:
            f.write(b'Test PNG content')
        
        # Store original values
        self.original_static_folder = app.static_folder
        
        # Set test values
        app.static_folder = self.static_dir
        app_module.static_folder = self.static_dir
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore original values
        app.static_folder = self.original_static_folder
        app_module.static_folder = self.original_static_folder
        
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_static_file_access(self):
        """Test accessing static files via different routes."""
        # Debug info
        print(f"Test directory: {self.test_dir}")
        print(f"Static directory: {self.static_dir}")
        print(f"Test file: {self.test_file}")
        print(f"Visualization directory: {self.test_vis_dir}")
        print(f"app.static_folder: {app.static_folder}")
        
        # Get test route information to see registered routes
        response = self.client.get('/api/test_route')
        print(f"Test route response: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print("Registered routes:")
            for route in data.get('routes', []):
                print(f"  {route}")
        
        # Test regular static file access
        response = self.client.get(f'/static/visualizations/{self.test_id}/test_page.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'Test PNG content')
        
        # Test API visualization route
        response = self.client.get(f'/api/visualizations/{self.test_id}/test_page.png')
        print(f"API response status: {response.status_code}")
        print(f"API response data: {response.data[:20]}...")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'Test PNG content')
    
    def test_static_file_not_found(self):
        """Test 404 responses for nonexistent files."""
        # Test regular static file access for nonexistent file
        response = self.client.get(f'/static/visualizations/{self.test_id}/nonexistent.png')
        self.assertEqual(response.status_code, 404)
        
        # Test API visualization route for nonexistent file
        response = self.client.get(f'/api/visualizations/{self.test_id}/nonexistent.png')
        self.assertEqual(response.status_code, 404)
    
    def test_static_debug_endpoint(self):
        """Test the static_debug endpoint."""
        response = self.client.get('/static_debug')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('static_folder', data)
        self.assertEqual(data['static_folder'], self.static_dir)
        self.assertIn('exists', data)
        self.assertTrue(data['exists'])
        self.assertIn('contents', data)


if __name__ == '__main__':
    unittest.main() 