"""
Integration test for the complete "Coffee in Dourdan" query flow
Tests the full LangGraph workflow with all enhancements
"""

import asyncio
import json
from app.services.langgraph_workflow_service import LangGraphWorkflowService

async def test_coffee_in_dourdan_integration():
    """Test the complete workflow for 'Je suis à Dourdan et je veux planter du café'"""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST: Coffee in Dourdan - Full Workflow")
    print("="*80)
    
    # Initialize the LangGraph workflow service
    print("\n📦 Initializing LangGraph Workflow Service...")
    workflow_service = LangGraphWorkflowService()
    
    # Test query
    query = "Je suis à Dourdan et je veux planter du café. Quelles sont vos recommandations ?"
    context = {}
    
    print(f"\n❓ Query: {query}")
    print(f"📍 Context: {context}")
    
    # Process the query through the workflow
    print("\n🔄 Processing query through LangGraph workflow...")
    result = await workflow_service.process_agricultural_query(query, context)
    
    print("\n" + "="*80)
    print("WORKFLOW RESULTS")
    print("="*80)
    
    # Check metadata
    metadata = result.get("metadata", {})
    print(f"\n📊 Metadata:")
    print(f"  - Agent Type: {metadata.get('agent_type', 'N/A')}")
    print(f"  - Confidence: {metadata.get('confidence', 'N/A')}")
    print(f"  - Processing Time: {metadata.get('processing_time', 'N/A')}s")
    print(f"  - Processing Steps: {metadata.get('processing_steps', [])}")
    
    # Check if weather data was collected
    if "weather_data" in metadata:
        print(f"\n🌤️  Weather Data Collected: ✅")
        weather = metadata["weather_data"]
        if isinstance(weather, dict) and "location" in weather:
            print(f"  - Location: {weather.get('location', 'N/A')}")
    
    # Check if feasibility data was collected
    if "feasibility_data" in metadata:
        print(f"\n🌱 Feasibility Data Collected: ✅")
        feasibility = metadata["feasibility_data"]
        if isinstance(feasibility, dict):
            print(f"  - Crop: {feasibility.get('crop', 'N/A')}")
            print(f"  - Location: {feasibility.get('location', 'N/A')}")
            print(f"  - Feasible: {feasibility.get('is_feasible', 'N/A')}")
            print(f"  - Score: {feasibility.get('feasibility_score', 'N/A')}/10")
            if "alternatives" in feasibility and feasibility["alternatives"]:
                print(f"  - Alternatives: {len(feasibility['alternatives'])} found")
    
    # Check response
    response = result.get("response", "")
    print(f"\n💬 Response Generated: {'✅' if response else '❌'}")
    print(f"   Length: {len(response)} characters")
    
    # Display response
    print("\n" + "="*80)
    print("GENERATED RESPONSE")
    print("="*80)
    print(response)
    print("="*80)
    
    # Validate response quality
    print("\n" + "="*80)
    print("RESPONSE QUALITY CHECKS")
    print("="*80)
    
    checks = {
        "Contains markdown headers (##)": "##" in response,
        "Contains emojis": any(emoji in response for emoji in ["🌱", "🌾", "⚠️", "✅", "❌", "🌡️", "💧", "⏱️", "💰", "🌳"]),
        "Contains bold text (**)": "**" in response,
        "Mentions Dourdan": "dourdan" in response.lower(),
        "Mentions café/coffee": "café" in response.lower() or "coffee" in response.lower(),
        "Contains specific temperatures": "°C" in response,
        "Contains alternatives": any(word in response.lower() for word in ["alternative", "figuier", "amandier", "vigne"]),
        "Contains recommendations": any(word in response.lower() for word in ["recommand", "conseil", "suggère"]),
        "Response length > 500 chars": len(response) > 500,
        "Contains structured sections": response.count("###") >= 3
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    print(f"\n📊 Quality Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    # Final assessment
    print("\n" + "="*80)
    if passed >= total * 0.8:  # 80% threshold
        print("✅ INTEGRATION TEST PASSED")
        print("="*80)
        return True
    else:
        print("❌ INTEGRATION TEST FAILED")
        print(f"   Only {passed}/{total} quality checks passed (need {int(total*0.8)}/{total})")
        print("="*80)
        return False

async def main():
    """Run the integration test"""
    try:
        success = await test_coffee_in_dourdan_integration()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Integration test failed with exception:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

