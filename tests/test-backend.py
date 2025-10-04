#!/usr/bin/env python3
"""
Simple test script to verify the Ekumen backend is working
"""

import requests
import json
import sys
import time

def test_backend():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Ekumen Backend...")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   📊 Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test 2: API documentation
    print("\n2. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ API docs accessible")
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API docs failed: {e}")
    
    # Test 3: OpenAPI schema
    print("\n3. Testing OpenAPI schema...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            print("   ✅ OpenAPI schema accessible")
            print(f"   📊 API Title: {schema.get('info', {}).get('title', 'Unknown')}")
            print(f"   📊 API Version: {schema.get('info', {}).get('version', 'Unknown')}")
        else:
            print(f"   ❌ OpenAPI schema failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ OpenAPI schema failed: {e}")
    
    # Test 4: Test a simple endpoint (if available)
    print("\n4. Testing available endpoints...")
    try:
        response = requests.get(f"{base_url}/api/v1/", timeout=5)
        if response.status_code == 200:
            print("   ✅ API v1 endpoint accessible")
        else:
            print(f"   ℹ️  API v1 endpoint returned: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ℹ️  API v1 endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Backend testing completed!")
    print("\n📋 Next steps:")
    print("   - Visit http://localhost:8000/docs for API documentation")
    print("   - Visit http://localhost:3000 for the frontend")
    print("   - Check the logs for any errors")
    
    return True

if __name__ == "__main__":
    print("Waiting for backend to start...")
    time.sleep(2)
    
    if test_backend():
        sys.exit(0)
    else:
        sys.exit(1)
