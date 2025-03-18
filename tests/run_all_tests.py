#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

# Set up Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Add directories to path
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, TESTS_DIR)

def run_unit_tests(specific_tests=None):
    """Run unit tests with pytest"""
    # Set PYTHONPATH for subprocess
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{BASE_DIR}:{TESTS_DIR}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = f"{BASE_DIR}:{TESTS_DIR}"
    
    cmd = ["python3", "-m", "pytest", "tests/unit"]
    if specific_tests:
        cmd.extend(specific_tests)
    print(f"Running unit tests: {' '.join(cmd)}")
    return subprocess.run(cmd, env=env).returncode

def run_integration_tests(specific_tests=None):
    """Run integration tests with pytest"""
    # Set PYTHONPATH for subprocess
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{BASE_DIR}:{TESTS_DIR}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = f"{BASE_DIR}:{TESTS_DIR}"
    
    cmd = ["python3", "-m", "pytest", "tests/integration"]
    if specific_tests:
        cmd.extend(specific_tests)
    print(f"Running integration tests: {' '.join(cmd)}")
    return subprocess.run(cmd, env=env).returncode

def run_visualization_tests():
    """Run visualization tests"""
    # Set PYTHONPATH for subprocess
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{BASE_DIR}:{TESTS_DIR}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = f"{BASE_DIR}:{TESTS_DIR}"
    
    print("Running visualization tests")
    return subprocess.run(["python3", "tests/run_visualization_tests.py"], env=env).returncode

def main():
    parser = argparse.ArgumentParser(description="Run tests for the PDF Checkbox POC")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--visualization", action="store_true", help="Run visualization tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--specific", nargs="+", help="Run specific test files")
    
    args = parser.parse_args()
    
    # If no arguments are specified, run all tests
    if not any([args.unit, args.integration, args.visualization, args.all, args.specific]):
        args.all = True
    
    results = []
    
    if args.all or args.unit:
        results.append(run_unit_tests(args.specific))
    
    if args.all or args.integration:
        results.append(run_integration_tests(args.specific))
    
    if args.all or args.visualization:
        results.append(run_visualization_tests())
    
    # Return non-zero exit code if any test failed
    return 1 if any(results) else 0

if __name__ == "__main__":
    sys.exit(main()) 