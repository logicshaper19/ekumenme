"""
Test script to verify dynamic examples refactoring works correctly.

This demonstrates that:
1. Weather ReAct examples are properly configured
2. Crop Health ReAct examples are properly configured
3. get_crop_health_react_prompt() uses dynamic examples
4. Examples are formatted correctly
"""

from app.prompts.dynamic_examples import get_dynamic_examples, get_example_stats
from app.prompts.crop_health_prompts import get_crop_health_react_prompt

def test_weather_react_examples():
    """Test Weather ReAct examples are available."""
    print("=" * 80)
    print("Testing Weather ReAct Examples")
    print("=" * 80)
    
    examples = get_dynamic_examples("WEATHER_REACT_PROMPT")
    
    if examples:
        print("✅ Weather ReAct examples found")
        print(f"\nExample length: {len(examples)} characters")
        print("\nFirst 500 characters:")
        print(examples[:500])
    else:
        print("❌ No Weather ReAct examples found")
    
    print("\n")

def test_crop_health_react_examples():
    """Test Crop Health ReAct examples are available."""
    print("=" * 80)
    print("Testing Crop Health ReAct Examples")
    print("=" * 80)
    
    examples = get_dynamic_examples("CROP_HEALTH_REACT_PROMPT")
    
    if examples:
        print("✅ Crop Health ReAct examples found")
        print(f"\nExample length: {len(examples)} characters")
        print("\nFirst 500 characters:")
        print(examples[:500])
    else:
        print("❌ No Crop Health ReAct examples found")
    
    print("\n")

def test_crop_health_prompt_integration():
    """Test that get_crop_health_react_prompt() uses dynamic examples."""
    print("=" * 80)
    print("Testing Crop Health Prompt Integration")
    print("=" * 80)

    # Get prompt with examples
    prompt_with_examples = get_crop_health_react_prompt(include_examples=True)

    # Get prompt without examples
    prompt_without_examples = get_crop_health_react_prompt(include_examples=False)

    # Extract system message
    system_with = str(prompt_with_examples.messages[0].prompt.template)
    system_without = str(prompt_without_examples.messages[0].prompt.template)

    print(f"✅ Prompt with examples: {len(system_with)} characters")
    print(f"✅ Prompt without examples: {len(system_without)} characters")
    print(f"✅ Difference: {len(system_with) - len(system_without)} characters")

    # Check if examples section is present
    if "EXEMPLES DE RAISONNEMENT" in system_with:
        print("✅ Examples section found in prompt with examples")
    else:
        print("❌ Examples section NOT found in prompt with examples")

    if "EXEMPLES DE RAISONNEMENT" not in system_without:
        print("✅ Examples section correctly absent in prompt without examples")
    else:
        print("❌ Examples section incorrectly present in prompt without examples")

    # Check for ReAct format in examples
    if "Thought:" in system_with and "Action:" in system_with:
        print("✅ ReAct format found in examples")
    else:
        print("❌ ReAct format NOT found in examples")

    # Check for proper MessagesPlaceholder usage
    if len(prompt_with_examples.messages) == 3:
        print("✅ Correct message structure (system, human, agent_scratchpad)")
    else:
        print(f"❌ Incorrect message structure: {len(prompt_with_examples.messages)} messages")

    # Check for single braces (not double)
    human_msg = str(prompt_with_examples.messages[1].prompt.template)
    if "{input}" in human_msg and "{{input}}" not in human_msg:
        print("✅ Correct template variable format (single braces)")
    else:
        print("❌ Incorrect template variable format (double braces found)")

    # Check that agent doesn't write Observation itself
    if "Le système te retournera automatiquement:" in system_with:
        print("✅ Correct ReAct format (agent doesn't write Observation)")
    else:
        print("❌ Incorrect ReAct format")

    print("\n")

def test_example_stats():
    """Test example statistics."""
    print("=" * 80)
    print("Example Library Statistics")
    print("=" * 80)
    
    stats = get_example_stats()
    
    for prompt_type, stat in stats.items():
        if "REACT" in prompt_type:
            print(f"\n{prompt_type}:")
            print(f"  Total examples: {stat['total_examples']}")
            print(f"  Example types: {[t.value for t in stat['example_types']]}")
            print(f"  Avg confidence: {stat['avg_confidence']:.2f}")
    
    print("\n")

if __name__ == "__main__":
    print("\n🧪 Dynamic Examples Refactoring Test Suite\n")
    
    test_weather_react_examples()
    test_crop_health_react_examples()
    test_crop_health_prompt_integration()
    test_example_stats()
    
    print("=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)

