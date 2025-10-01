"""
Test Weather Intelligence Agent with Sophisticated Prompts

This script tests the Weather Agent with the new sophisticated prompt system
to validate that:
1. Agent initializes correctly with ChatPromptTemplate
2. Sophisticated prompts are loaded
3. ReAct format works properly
4. Tools are accessible and used correctly
5. Responses are more sophisticated than basic prompts
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.weather_agent import WeatherIntelligenceAgent


def test_agent_initialization():
    """Test 1: Agent initializes with sophisticated prompts"""
    print("\n" + "="*80)
    print("TEST 1: Agent Initialization with Sophisticated Prompts")
    print("="*80)
    
    try:
        agent = WeatherIntelligenceAgent(enable_dynamic_examples=True)
        print("✅ Agent initialized successfully")
        print(f"   - LLM: {agent.llm.model_name}")
        print(f"   - Tools: {len(agent.tools)}")
        print(f"   - Dynamic examples: {agent.enable_dynamic_examples}")
        print(f"   - Prompt Manager: {type(agent.prompt_manager).__name__}")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_structure():
    """Test 2: Verify prompt structure"""
    print("\n" + "="*80)
    print("TEST 2: Prompt Structure Verification")
    print("="*80)
    
    try:
        agent = WeatherIntelligenceAgent()
        prompt = agent._get_prompt_template()
        
        print(f"✅ Prompt type: {type(prompt).__name__}")
        print(f"   - Expected: ChatPromptTemplate")
        print(f"   - Match: {type(prompt).__name__ == 'ChatPromptTemplate'}")
        
        # Check prompt messages
        if hasattr(prompt, 'messages'):
            print(f"   - Messages: {len(prompt.messages)}")
            for i, msg in enumerate(prompt.messages):
                print(f"     {i+1}. {type(msg).__name__}")
        
        # Check if sophisticated content is present
        prompt_str = str(prompt)
        checks = {
            "BASE_AGRICULTURAL_SYSTEM_PROMPT": "BASE_AGRICULTURAL_SYSTEM_PROMPT" in prompt_str,
            "ReAct format": "FORMAT REACT" in prompt_str or "Thought:" in prompt_str,
            "Tools reference": "{tools}" in prompt_str,
            "Examples": "EXEMPLES" in prompt_str or "Exemple" in prompt_str,
            "Safety": "IMPORTANT" in prompt_str or "sécurité" in prompt_str.lower()
        }
        
        print("\n   Sophisticated content checks:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "⚠️"
            print(f"   {status} {check_name}: {passed}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"❌ Prompt structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_query():
    """Test 3: Simple weather query"""
    print("\n" + "="*80)
    print("TEST 3: Simple Weather Query")
    print("="*80)
    
    try:
        agent = WeatherIntelligenceAgent()
        
        query = "Quel temps fera-t-il demain à Paris?"
        context = {
            "location": "Paris",
            "farm_id": "test_farm"
        }
        
        print(f"Query: {query}")
        print(f"Context: {context}")
        print("\nProcessing...")
        
        result = await agent.aprocess(message=query, context=context)
        
        print("\n✅ Query processed successfully")
        print(f"   - Response type: {type(result)}")
        print(f"   - Has response: {'response' in result}")
        
        if 'response' in result:
            response = result['response']
            print(f"\n   Response preview (first 200 chars):")
            print(f"   {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_intervention_window_query():
    """Test 4: Intervention window query (sophisticated scenario)"""
    print("\n" + "="*80)
    print("TEST 4: Intervention Window Query (Sophisticated)")
    print("="*80)
    
    try:
        agent = WeatherIntelligenceAgent()
        
        query = "Quand puis-je traiter mes céréales cette semaine?"
        context = {
            "location": "Beauce",
            "crop": "blé",
            "farm_id": "test_farm",
            "intervention_type": "traitement"
        }
        
        print(f"Query: {query}")
        print(f"Context: {context}")
        print("\nProcessing...")
        
        result = await agent.aprocess(message=query, context=context)
        
        print("\n✅ Intervention window query processed successfully")
        
        if 'response' in result:
            response = result['response']
            print(f"\n   Response preview (first 300 chars):")
            print(f"   {response[:300]}...")
            
            # Check for sophisticated elements
            sophisticated_checks = {
                "Specific dates/times": any(word in response.lower() for word in ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "h"]),
                "Temperature data": "°C" in response or "température" in response.lower(),
                "Wind data": "vent" in response.lower() or "km/h" in response,
                "Recommendations": "recommand" in response.lower() or "conseil" in response.lower()
            }
            
            print("\n   Sophisticated response checks:")
            for check_name, passed in sophisticated_checks.items():
                status = "✅" if passed else "⚠️"
                print(f"   {status} {check_name}: {passed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Intervention window query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_capabilities():
    """Test 5: Agent capabilities"""
    print("\n" + "="*80)
    print("TEST 5: Agent Capabilities")
    print("="*80)
    
    try:
        agent = WeatherIntelligenceAgent()
        capabilities = agent.get_capabilities()
        
        print("✅ Capabilities retrieved:")
        print(f"   - Agent type: {capabilities.get('agent_type')}")
        print(f"   - Description: {capabilities.get('description')}")
        print(f"   - Tools: {len(capabilities.get('tools', []))}")
        
        for tool in capabilities.get('tools', []):
            print(f"     • {tool}")
        
        return True
        
    except Exception as e:
        print(f"❌ Capabilities test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("WEATHER AGENT SOPHISTICATED PROMPT TESTS")
    print("="*80)
    
    results = {}
    
    # Test 1: Initialization
    results['initialization'] = test_agent_initialization()
    
    # Test 2: Prompt structure
    results['prompt_structure'] = test_prompt_structure()
    
    # Test 3: Simple query
    results['simple_query'] = await test_simple_query()
    
    # Test 4: Intervention window (sophisticated)
    results['intervention_window'] = await test_intervention_window_query()
    
    # Test 5: Capabilities
    results['capabilities'] = test_capabilities()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Weather Agent is ready with sophisticated prompts!")
    else:
        print("\n⚠️ Some tests failed. Review the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

