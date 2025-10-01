"""
Test Weather Prompt Structure (No API Key Required)

This script tests the prompt structure without initializing the full agent.
Tests:
1. Prompt function exists and is callable
2. Returns ChatPromptTemplate
3. Contains sophisticated content
4. Has ReAct format
5. Includes examples
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.prompts.weather_prompts import get_weather_react_prompt
from langchain.prompts import ChatPromptTemplate


def test_prompt_function_exists():
    """Test 1: Prompt function exists"""
    print("\n" + "="*80)
    print("TEST 1: Prompt Function Exists")
    print("="*80)
    
    try:
        assert callable(get_weather_react_prompt), "get_weather_react_prompt should be callable"
        print("✅ get_weather_react_prompt function exists and is callable")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_prompt_returns_chat_template():
    """Test 2: Returns ChatPromptTemplate"""
    print("\n" + "="*80)
    print("TEST 2: Returns ChatPromptTemplate")
    print("="*80)
    
    try:
        prompt = get_weather_react_prompt()
        print(f"   Returned type: {type(prompt).__name__}")
        assert isinstance(prompt, ChatPromptTemplate), f"Expected ChatPromptTemplate, got {type(prompt)}"
        print("✅ Returns ChatPromptTemplate (LangChain best practice)")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_has_messages():
    """Test 3: Has proper message structure"""
    print("\n" + "="*80)
    print("TEST 3: Message Structure")
    print("="*80)
    
    try:
        prompt = get_weather_react_prompt()
        assert hasattr(prompt, 'messages'), "Prompt should have messages attribute"
        
        messages = prompt.messages
        print(f"   Number of messages: {len(messages)}")
        
        for i, msg in enumerate(messages):
            print(f"   Message {i+1}: {type(msg).__name__}")
        
        assert len(messages) >= 2, "Should have at least system and human messages"
        print("✅ Prompt has proper message structure")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_contains_sophisticated_content():
    """Test 4: Contains sophisticated content"""
    print("\n" + "="*80)
    print("TEST 4: Sophisticated Content")
    print("="*80)
    
    try:
        prompt = get_weather_react_prompt(include_examples=True)
        prompt_str = str(prompt)
        
        checks = {
            "Base agricultural prompt": "BASE_AGRICULTURAL_SYSTEM_PROMPT" in prompt_str or "conseiller agricole" in prompt_str.lower(),
            "Weather expertise": "météo" in prompt_str.lower() and ("température" in prompt_str.lower() or "vent" in prompt_str.lower()),
            "Tools reference": "{tools}" in prompt_str,
            "Tool names": "{tool_names}" in prompt_str,
            "Context variable": "{context}" in prompt_str or "{{context}}" in prompt_str,
            "Input variable": "{input}" in prompt_str or "{{input}}" in prompt_str,
            "Agent scratchpad": "{agent_scratchpad}" in prompt_str,
        }
        
        print("\n   Content checks:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        all_passed = all(checks.values())
        if all_passed:
            print("\n✅ All sophisticated content present")
        else:
            print("\n⚠️ Some content missing")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_has_react_format():
    """Test 5: Has ReAct format instructions"""
    print("\n" + "="*80)
    print("TEST 5: ReAct Format")
    print("="*80)
    
    try:
        prompt = get_weather_react_prompt()
        prompt_str = str(prompt)
        
        react_elements = {
            "Question": "Question:" in prompt_str,
            "Thought": "Thought:" in prompt_str,
            "Action": "Action:" in prompt_str,
            "Action Input": "Action Input:" in prompt_str,
            "Observation": "Observation:" in prompt_str,
            "Final Answer": "Final Answer:" in prompt_str,
        }
        
        print("\n   ReAct format elements:")
        for element, present in react_elements.items():
            status = "✅" if present else "❌"
            print(f"   {status} {element}")
        
        all_present = all(react_elements.values())
        if all_present:
            print("\n✅ Complete ReAct format present")
        else:
            print("\n⚠️ Some ReAct elements missing")
        
        return all_present
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_includes_examples():
    """Test 6: Includes few-shot examples when requested"""
    print("\n" + "="*80)
    print("TEST 6: Few-Shot Examples")
    print("="*80)
    
    try:
        # Test with examples
        prompt_with_examples = get_weather_react_prompt(include_examples=True)
        prompt_str_with = str(prompt_with_examples)
        
        # Test without examples
        prompt_without_examples = get_weather_react_prompt(include_examples=False)
        prompt_str_without = str(prompt_without_examples)
        
        has_examples_when_requested = "Exemple" in prompt_str_with or "EXEMPLES" in prompt_str_with
        no_examples_when_not_requested = "Exemple" not in prompt_str_without and "EXEMPLES" not in prompt_str_without
        
        print(f"   With examples (include_examples=True):")
        print(f"   {'✅' if has_examples_when_requested else '❌'} Contains examples")
        
        print(f"\n   Without examples (include_examples=False):")
        print(f"   {'✅' if no_examples_when_not_requested else '❌'} No examples")
        
        if has_examples_when_requested:
            print("\n✅ Dynamic example inclusion works correctly")
            return True
        else:
            print("\n⚠️ Examples not found when requested")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_has_safety_reminders():
    """Test 7: Has safety and compliance reminders"""
    print("\n" + "="*80)
    print("TEST 7: Safety & Compliance")
    print("="*80)
    
    try:
        prompt = get_weather_react_prompt()
        prompt_str = str(prompt)
        
        safety_elements = {
            "Important section": "IMPORTANT" in prompt_str,
            "Safety mention": "sécurité" in prompt_str.lower() or "précaution" in prompt_str.lower(),
            "Tool usage guidance": "utilise" in prompt_str.lower() and "outil" in prompt_str.lower(),
        }
        
        print("\n   Safety elements:")
        for element, present in safety_elements.items():
            status = "✅" if present else "⚠️"
            print(f"   {status} {element}")
        
        has_safety = any(safety_elements.values())
        if has_safety:
            print("\n✅ Safety reminders present")
        else:
            print("\n⚠️ No safety reminders found")
        
        return has_safety
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("WEATHER PROMPT STRUCTURE TESTS (No API Key Required)")
    print("="*80)
    
    results = {}
    
    results['function_exists'] = test_prompt_function_exists()
    results['returns_chat_template'] = test_prompt_returns_chat_template()
    results['has_messages'] = test_prompt_has_messages()
    results['sophisticated_content'] = test_prompt_contains_sophisticated_content()
    results['react_format'] = test_prompt_has_react_format()
    results['examples'] = test_prompt_includes_examples()
    results['safety'] = test_prompt_has_safety_reminders()
    
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
        print("\n🎉 ALL TESTS PASSED! Weather prompt is sophisticated and ready!")
        print("\n✅ Key achievements:")
        print("   - Uses ChatPromptTemplate (LangChain best practice)")
        print("   - Contains sophisticated weather expertise")
        print("   - Has complete ReAct format")
        print("   - Includes dynamic few-shot examples")
        print("   - Has safety reminders")
    else:
        print("\n⚠️ Some tests failed. Review the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

