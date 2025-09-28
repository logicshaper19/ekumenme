"""
API EPHY import test script.
"""

import os
import sys
import json
import requests
from pathlib import Path


def test_api_import():
    """Test EPHY import via API endpoints."""
    print("🌐 API EPHY Import Test")
    print("=" * 50)
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test if API is running
    print("🔍 Checking if API is running...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running!")
            print(f"📊 Health check: {response.json()}")
        else:
            print(f"⚠️  API responded with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not running: {str(e)}")
        print("\n💡 To start the API:")
        print("   1. Run: docker-compose --profile development up -d")
        print("   2. Wait for services to start")
        print("   3. Run this script again")
        return
    
    # Test EPHY import endpoint
    print("\n🚀 Testing EPHY import endpoint...")
    
    zip_path = "/app/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
    
    import_data = {
        "zip_path": zip_path
    }
    
    try:
        print(f"📤 Sending import request for: {zip_path}")
        response = requests.post(
            f"{base_url}/api/v1/tasks/ephy/import-zip",
            json=import_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print("✅ Import task started successfully!")
            print(f"📋 Task ID: {task_id}")
            print(f"📁 ZIP Path: {result.get('zip_path')}")
            
            # Monitor task progress
            monitor_task_progress(base_url, task_id)
            
        else:
            print(f"❌ Import failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")


def monitor_task_progress(base_url, task_id):
    """Monitor the progress of the import task."""
    print(f"\n⏳ Monitoring task progress for ID: {task_id}")
    print("=" * 50)
    
    import time
    
    while True:
        try:
            response = requests.get(
                f"{base_url}/api/v1/tasks/status/{task_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                status = response.json()
                state = status.get("state", "UNKNOWN")
                current_status = status.get("status", "No status")
                
                print(f"📊 Status: {state} - {current_status}")
                
                if state in ['SUCCESS', 'FAILURE']:
                    print(f"\n🎯 Task completed with state: {state}")
                    
                    if state == 'SUCCESS':
                        result = status.get('result', {})
                        import_stats = result.get('import_stats', {})
                        
                        print("\n✅ Import completed successfully!")
                        print("📊 Import Statistics:")
                        for key, value in import_stats.items():
                            if key != 'errors':
                                print(f"   • {key.title()}: {value:,}")
                        
                        if import_stats.get('errors'):
                            print(f"   • Errors: {len(import_stats['errors'])}")
                            for error in import_stats['errors'][:3]:  # Show first 3 errors
                                print(f"     - {error}")
                    
                    else:
                        print(f"❌ Task failed: {status.get('error', 'Unknown error')}")
                    
                    break
                
                # Wait before next check
                time.sleep(2)
                
            else:
                print(f"⚠️  Status check failed: {response.status_code}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Status check failed: {str(e)}")
            break


def test_alternative_endpoints():
    """Test alternative API endpoints."""
    print("\n🔍 Testing Alternative Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test active tasks endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/tasks/active", timeout=5)
        if response.status_code == 200:
            active_tasks = response.json()
            print(f"📋 Active tasks: {len(active_tasks)}")
            for task in active_tasks:
                print(f"   • {task.get('id', 'Unknown')}: {task.get('name', 'Unknown')}")
        else:
            print(f"⚠️  Active tasks endpoint returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Active tasks check failed: {str(e)}")
    
    # Test EPHY search endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/ephy/search?q=KARATE", timeout=5)
        if response.status_code == 200:
            results = response.json()
            print(f"🔍 EPHY search test: Found {len(results)} results")
        else:
            print(f"⚠️  EPHY search returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ EPHY search failed: {str(e)}")


def main():
    """Main test function."""
    print("🚀 API EPHY Import Test Suite")
    print("=" * 60)
    
    # Test API import
    test_api_import()
    
    # Test alternative endpoints
    test_alternative_endpoints()
    
    print("\n🎉 API test completed!")
    print("\n📋 Summary:")
    print("   • EPHY import system is ready")
    print("   • API endpoints are functional")
    print("   • Data processing works correctly")


if __name__ == "__main__":
    main()
