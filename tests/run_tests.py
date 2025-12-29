#!/usr/bin/env python3
"""
Test Runner for AI Exam Proctoring System
Run all tests or specific test files
"""

import os
import sys
import subprocess

def run_test(test_file):
    """Run a specific test file"""
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd='tests')
        print(f"Running {test_file}:")
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to run {test_file}: {e}")
        return False

def main():
    """Run all tests in the tests directory"""
    test_files = [f for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')]
    
    if not test_files:
        print("No test files found in tests directory")
        return
    
    print("Running AI Exam Proctoring System Tests...")
    print("=" * 50)
    
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        if run_test(test_file):
            passed += 1
        print("-" * 30)
    
    print(f"Tests completed: {passed}/{total} passed")

if __name__ == "__main__":
    main()