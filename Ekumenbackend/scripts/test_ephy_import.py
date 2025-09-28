"""
Test script for EPHY import functionality.
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ephy_import import EPHYImporter


def test_ephy_import():
    """Test EPHY import functionality."""
    print("🧪 Testing EPHY Import Functionality")
    print("=" * 50)
    
    # Path to the EPHY ZIP file
    zip_path = "/Users/elisha/ekumenme/agricultural-backend/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
    
    if not os.path.exists(zip_path):
        print(f"❌ ZIP file not found: {zip_path}")
        return
    
    print(f"📁 Found EPHY ZIP file: {os.path.basename(zip_path)}")
    print(f"📊 File size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
    
    try:
        # Initialize importer
        print("\n🔄 Initializing EPHY importer...")
        importer = EPHYImporter()
        
        # Import data
        print("📥 Starting import process...")
        result = importer.import_zip_file(zip_path)
        
        # Display results
        print("\n✅ Import completed successfully!")
        print("📊 Import Statistics:")
        print(f"   • Products imported: {result.get('produits', 0)}")
        print(f"   • Substances imported: {result.get('substances', 0)}")
        print(f"   • Titulaires imported: {result.get('titulaires', 0)}")
        print(f"   • Usages imported: {result.get('usages', 0)}")
        print(f"   • Errors: {len(result.get('errors', []))}")
        
        if result.get('errors'):
            print("\n⚠️  Errors encountered:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
        
        importer.close()
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_api_import():
    """Test EPHY import via API."""
    print("\n🌐 Testing EPHY Import via API")
    print("=" * 50)
    
    zip_path = "/Users/elisha/ekumenme/agricultural-backend/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
    
    try:
        async with httpx.AsyncClient() as client:
            # Start import task
            print("🚀 Starting import task via API...")
            response = await client.post(
                "http://localhost:8000/api/v1/tasks/ephy/import-zip",
                json={"zip_path": zip_path}
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                print(f"✅ Task started successfully!")
                print(f"📋 Task ID: {task_id}")
                
                # Monitor task progress
                print("\n⏳ Monitoring task progress...")
                while True:
                    status_response = await client.get(
                        f"http://localhost:8000/api/v1/tasks/status/{task_id}"
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"📊 Status: {status['state']} - {status['status']}")
                        
                        if status['state'] in ['SUCCESS', 'FAILURE']:
                            break
                    
                    await asyncio.sleep(2)
                
                print("✅ Task completed!")
                
            else:
                print(f"❌ Failed to start task: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")


def main():
    """Main test function."""
    print("🚀 EPHY Import Test Suite")
    print("=" * 60)
    
    # Test direct import
    test_ephy_import()
    
    # Ask if user wants to test API
    print("\n" + "=" * 60)
    response = input("🌐 Do you want to test the API import? (y/n): ")
    
    if response.lower() == 'y':
        try:
            asyncio.run(test_api_import())
        except KeyboardInterrupt:
            print("\n⏹️  Test interrupted by user")
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")
    
    print("\n🎉 Test suite completed!")


if __name__ == "__main__":
    main()
