import requests
import json

def test_minimal_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Minimal Agricultural API")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test root endpoint
    print("2. Testing root endpoint...")
    response = requests.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test seeding sample data
    print("3. Seeding sample data...")
    response = requests.post(f"{base_url}/api/v1/seed-sample-data")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test getting exploitations
    print("4. Getting exploitations...")
    response = requests.get(f"{base_url}/api/v1/exploitations")
    print(f"   Status: {response.status_code}")
    print(f"   Count: {len(response.json())}")
    print()
    
    # Test getting parcelles
    print("5. Getting parcelles...")
    response = requests.get(f"{base_url}/api/v1/parcelles")
    parcelles = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Count: {len(parcelles)}")
    print()
    
    # Test getting interventions
    print("6. Getting interventions...")
    response = requests.get(f"{base_url}/api/v1/interventions")
    interventions = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Count: {len(interventions)}")
    print()
    
    # Test compliance check
    if interventions:
        print("7. Testing compliance check...")
        intervention_id = interventions[0]["uuid_intervention"]
        response = requests.get(f"{base_url}/api/v1/compliance/intervention/{intervention_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Compliant: {response.json().get('compliant')}")
        print()
    
    # Test MesParcelles sync simulation
    print("8. Testing MesParcelles sync simulation...")
    response = requests.post(f"{base_url}/api/v1/sync/mesparcelles/12345678901234")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test stats
    print("9. Getting final stats...")
    response = requests.get(f"{base_url}/api/v1/stats")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    print("✅ All tests completed!")
    print("🌐 Visit http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    test_minimal_api()
