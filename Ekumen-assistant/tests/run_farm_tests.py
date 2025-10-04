#!/usr/bin/env python3
"""
Test runner for farm data functionality
Runs all tests related to farm data validation, WebSocket, and API endpoints
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all farm-related tests"""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Test files to run
    test_files = [
        "tests/unit/test_farm_data_validator.py",
        "tests/unit/test_farm_websocket.py", 
        "tests/unit/test_farm_api.py"
    ]
    
    print("🧪 Running Farm Data Tests")
    print("=" * 50)
    
    all_passed = True
    
    for test_file in test_files:
        print(f"\n📋 Running {test_file}...")
        print("-" * 30)
        
        try:
            # Run pytest for the specific test file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v",  # Verbose output
                "--tb=short",  # Short traceback format
                "--no-header",  # No pytest header
                "--disable-warnings"  # Disable warnings for cleaner output
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"❌ {test_file} - FAILED")
                if result.stdout:
                    print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - TIMEOUT (300s)")
            all_passed = False
        except Exception as e:
            print(f"💥 {test_file} - ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All farm data tests PASSED!")
        return 0
    else:
        print("💥 Some farm data tests FAILED!")
        return 1

def run_specific_test_category(category):
    """Run tests for a specific category"""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    test_mapping = {
        "validation": "tests/unit/test_farm_data_validator.py",
        "websocket": "tests/unit/test_farm_websocket.py",
        "api": "tests/unit/test_farm_api.py"
    }
    
    if category not in test_mapping:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(test_mapping.keys())}")
        return 1
    
    test_file = test_mapping[category]
    print(f"🧪 Running {category} tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, 
            "-v",
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ], timeout=300)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {category} tests - TIMEOUT (300s)")
        return 1
    except Exception as e:
        print(f"💥 {category} tests - ERROR: {e}")
        return 1

def run_coverage_tests():
    """Run tests with coverage reporting"""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 Running Farm Data Tests with Coverage")
    print("=" * 50)
    
    test_files = [
        "tests/unit/test_farm_data_validator.py",
        "tests/unit/test_farm_websocket.py", 
        "tests/unit/test_farm_api.py"
    ]
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            *test_files,
            "--cov=app.services.validation",
            "--cov=app.api.v1.farm",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v",
            "--tb=short"
        ], timeout=600)
        
        if result.returncode == 0:
            print("\n✅ Coverage report generated in htmlcov/")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("⏰ Coverage tests - TIMEOUT (600s)")
        return 1
    except Exception as e:
        print(f"💥 Coverage tests - ERROR: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validation":
            exit_code = run_specific_test_category("validation")
        elif command == "websocket":
            exit_code = run_specific_test_category("websocket")
        elif command == "api":
            exit_code = run_specific_test_category("api")
        elif command == "coverage":
            exit_code = run_coverage_tests()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: validation, websocket, api, coverage")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
