"""
Test Simple Weather Query
Verify that "Quelle est la météo à Dourdan?" gets a concise response
"""

import asyncio
import sys
from app.services.langgraph_workflow_service import LangGraphWorkflowService

async def test_simple_weather_query():
    """Test that simple weather query gets concise response"""
    print("\n" + "="*80)
    print("TEST: Simple Weather Query")
    print("="*80)
    
    # Initialize service
    service = LangGraphWorkflowService()
    
    # Test query
    query = "Quelle est la météo à Dourdan ?"
    print(f"\n📝 Query: {query}")
    print("-" * 80)
    
    # Process query
    print("\n⏳ Processing...")
    result = await service.process_agricultural_query(query)

    print(f"\n🔍 Debug - Result type: {type(result)}")
    print(f"🔍 Debug - Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
    if isinstance(result, dict) and "messages" in result:
        print(f"🔍 Debug - Messages count: {len(result['messages'])}")

    # Extract response
    if result and "response" in result and result["response"]:
        response = result["response"]
        
        print("\n✅ Response received:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
        # Analyze response
        response_length = len(response)
        num_sections = response.count("###")
        num_sentences = response.count(".") + response.count("!") + response.count("?")
        
        print(f"\n📊 Response Analysis:")
        print(f"   - Length: {response_length} characters")
        print(f"   - Sections (###): {num_sections}")
        print(f"   - Sentences: {num_sentences}")
        
        # Check if response is concise
        is_concise = response_length < 800  # Should be much shorter than 2540
        has_few_sections = num_sections <= 2  # Should not have 6 sections
        has_weather_data = "température" in response.lower() or "°c" in response.lower()
        mentions_dourdan = "dourdan" in response.lower()
        
        print(f"\n✅ Quality Checks:")
        print(f"   {'✅' if is_concise else '❌'} Concise (< 800 chars): {is_concise}")
        print(f"   {'✅' if has_few_sections else '❌'} Few sections (≤ 2): {has_few_sections}")
        print(f"   {'✅' if has_weather_data else '❌'} Contains weather data: {has_weather_data}")
        print(f"   {'✅' if mentions_dourdan else '❌'} Mentions Dourdan: {mentions_dourdan}")
        
        # Overall verdict
        all_passed = is_concise and has_few_sections and has_weather_data and mentions_dourdan
        
        print(f"\n{'='*80}")
        if all_passed:
            print("✅ TEST PASSED: Simple query got concise response!")
        else:
            print("❌ TEST FAILED: Response is still too complex")
        print("="*80)
        
        # Show classification info if available
        if "context" in result:
            print(f"\n📋 Classification Info:")
            for key, value in result.get("context", {}).items():
                print(f"   - {key}: {value}")
        
        return all_passed
    else:
        print("\n❌ ERROR: No response received")
        return False


async def test_complex_query_comparison():
    """Compare with complex query to ensure it still gets full structure"""
    print("\n" + "="*80)
    print("TEST: Complex Query (for comparison)")
    print("="*80)
    
    service = LangGraphWorkflowService()
    
    query = "Je veux planter du café à Dourdan"
    print(f"\n📝 Query: {query}")
    print("-" * 80)
    
    print("\n⏳ Processing...")
    result = await service.process_agricultural_query(query)
    
    if result and "response" in result and result["response"]:
        response = result["response"]
        
        response_length = len(response)
        num_sections = response.count("###")
        
        print(f"\n📊 Response Analysis:")
        print(f"   - Length: {response_length} characters")
        print(f"   - Sections (###): {num_sections}")
        
        # Complex query should have full structure
        is_detailed = response_length > 1000
        has_many_sections = num_sections >= 4
        
        print(f"\n✅ Quality Checks:")
        print(f"   {'✅' if is_detailed else '❌'} Detailed (> 1000 chars): {is_detailed}")
        print(f"   {'✅' if has_many_sections else '❌'} Multiple sections (≥ 4): {has_many_sections}")
        
        all_passed = is_detailed and has_many_sections
        
        print(f"\n{'='*80}")
        if all_passed:
            print("✅ TEST PASSED: Complex query got full structure!")
        else:
            print("⚠️  WARNING: Complex query response may be too short")
        print("="*80)
        
        return all_passed
    else:
        print("\n❌ ERROR: No response received")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SIMPLE VS COMPLEX QUERY RESPONSE TEST")
    print("="*80)
    
    # Test 1: Simple weather query
    simple_passed = await test_simple_weather_query()
    
    # Test 2: Complex cultivation query
    complex_passed = await test_complex_query_comparison()
    
    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Simple query test: {'✅ PASSED' if simple_passed else '❌ FAILED'}")
    print(f"Complex query test: {'✅ PASSED' if complex_passed else '❌ FAILED'}")
    
    if simple_passed and complex_passed:
        print("\n🎉 ALL TESTS PASSED! Query complexity routing is working correctly!")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

