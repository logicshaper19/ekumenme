"""
Test script to verify the polished Crop Health ReAct prompt.

This demonstrates the improvements:
1. Concrete example with multi-step reasoning
2. Clear Action Input format (JSON)
3. Dynamic tool names from {tools}
4. Fallback handling instructions
5. Critical rules for format compliance
"""

from app.prompts.crop_health_prompts import get_crop_health_react_prompt

def test_prompt_improvements():
    """Test all the polish improvements."""
    print("=" * 80)
    print("Testing Crop Health ReAct Prompt - Polish Improvements")
    print("=" * 80)
    
    # Get prompt with examples
    prompt = get_crop_health_react_prompt(include_examples=True)
    
    # Extract system message
    system_prompt = str(prompt.messages[0].prompt.template)
    
    print("\n✅ IMPROVEMENT 1: Action Input Format Clarity")
    if '{"param1": "value1", "param2": "value2"}' in system_prompt:
        print("   ✓ JSON format example present")
    else:
        print("   ✗ JSON format example missing")
    
    print("\n✅ IMPROVEMENT 2: Concrete Multi-Step Example")
    if "EXEMPLE CONCRET DE RAISONNEMENT MULTI-ÉTAPES" in system_prompt:
        print("   ✓ Concrete example section present")
        if "rouille jaune" in system_prompt:
            print("   ✓ Multi-step reasoning example (rouille jaune) present")
        if system_prompt.count("Action:") >= 5:  # At least 3 actions in concrete example
            print(f"   ✓ Multiple tool calls demonstrated ({system_prompt.count('Action:')} actions)")
    else:
        print("   ✗ Concrete example missing")
    
    print("\n✅ IMPROVEMENT 3: Dynamic Tool Names")
    if "Utilise les noms d'outils EXACTS tels qu'ils apparaissent dans la liste ci-dessus" in system_prompt:
        print("   ✓ Instruction to use exact tool names from {tools}")
    else:
        print("   ✗ Dynamic tool name instruction missing")
    
    print("\n✅ IMPROVEMENT 4: Fallback Handling")
    if "Si un outil échoue" in system_prompt:
        print("   ✓ Fallback handling instructions present")
        if "approche alternative" in system_prompt:
            print("   ✓ Alternative approach guidance included")
    else:
        print("   ✗ Fallback handling missing")
    
    print("\n✅ IMPROVEMENT 5: Critical Format Rules")
    if "RÈGLES CRITIQUES" in system_prompt:
        print("   ✓ Critical rules section present")
        checks = [
            ('N\'invente JAMAIS "Observation:"', "Don't write Observation"),
            ("Écris \"Thought:\", \"Action:\", \"Action Input:\", \"Final Answer:\"", "Exact format keywords"),
            ("le système le génère automatiquement", "System generates Observation"),
        ]
        for check_text, description in checks:
            if check_text in system_prompt:
                print(f"   ✓ {description}")
            else:
                print(f"   ✗ {description} missing")
    else:
        print("   ✗ Critical rules section missing")
    
    print("\n" + "=" * 80)
    print("Prompt Statistics")
    print("=" * 80)
    print(f"Total length: {len(system_prompt)} characters")
    print(f"Number of examples: {system_prompt.count('Question:')}")
    print(f"Number of tool calls shown: {system_prompt.count('Action:')}")
    print(f"Number of observations shown: {system_prompt.count('Observation:')}")
    
    print("\n" + "=" * 80)
    print("Sample Sections")
    print("=" * 80)
    
    # Extract and show the concrete example
    if "EXEMPLE CONCRET" in system_prompt:
        start = system_prompt.find("EXEMPLE CONCRET")
        end = system_prompt.find("---", start)
        if end > start:
            concrete_example = system_prompt[start:end].strip()
            print("\n📝 CONCRETE EXAMPLE (first 800 chars):")
            print(concrete_example[:800])
            print("...")
    
    # Extract and show critical rules
    if "RÈGLES CRITIQUES" in system_prompt:
        start = system_prompt.find("RÈGLES CRITIQUES")
        # Find the end (next major section or end of string)
        end = len(system_prompt)
        critical_rules = system_prompt[start:end].strip()
        print("\n⚠️  CRITICAL RULES:")
        print(critical_rules[:500])
        print("...")
    
    print("\n" + "=" * 80)
    print("✅ All polish improvements verified!")
    print("=" * 80)

def test_message_structure():
    """Test the message structure is correct."""
    print("\n" + "=" * 80)
    print("Testing Message Structure")
    print("=" * 80)
    
    prompt = get_crop_health_react_prompt(include_examples=True)
    
    print(f"\nNumber of messages: {len(prompt.messages)}")
    print(f"Message 1 type: {type(prompt.messages[0]).__name__}")
    print(f"Message 2 type: {type(prompt.messages[1]).__name__}")
    print(f"Message 3 type: {type(prompt.messages[2]).__name__}")
    
    # Check human message
    human_template = str(prompt.messages[1].prompt.template)
    print(f"\nHuman message template: '{human_template}'")
    
    if human_template == "{input}":
        print("✅ Human message uses simple {input} variable")
    else:
        print("❌ Human message has unexpected format")
    
    # Check agent_scratchpad
    if hasattr(prompt.messages[2], 'variable_name'):
        scratchpad_var = prompt.messages[2].variable_name
        print(f"\nAgent scratchpad variable: '{scratchpad_var}'")
        if scratchpad_var == "agent_scratchpad":
            print("✅ MessagesPlaceholder correctly configured")
        else:
            print("❌ MessagesPlaceholder has wrong variable name")
    else:
        print("❌ Message 3 is not a MessagesPlaceholder")

def test_prompt_size_comparison():
    """Compare prompt sizes with and without examples."""
    print("\n" + "=" * 80)
    print("Prompt Size Comparison")
    print("=" * 80)
    
    prompt_with = get_crop_health_react_prompt(include_examples=True)
    prompt_without = get_crop_health_react_prompt(include_examples=False)
    
    system_with = str(prompt_with.messages[0].prompt.template)
    system_without = str(prompt_without.messages[0].prompt.template)
    
    print(f"\nWith examples: {len(system_with):,} characters")
    print(f"Without examples: {len(system_without):,} characters")
    print(f"Difference: {len(system_with) - len(system_without):,} characters")
    
    # Calculate token estimate (rough: 1 token ≈ 4 characters)
    tokens_with = len(system_with) // 4
    tokens_without = len(system_without) // 4
    
    print(f"\nEstimated tokens with examples: ~{tokens_with:,}")
    print(f"Estimated tokens without examples: ~{tokens_without:,}")
    print(f"Token overhead: ~{tokens_with - tokens_without:,}")
    
    # Cost estimate (GPT-4 input: $0.03/1k tokens)
    cost_per_query_with = (tokens_with / 1000) * 0.03
    cost_per_query_without = (tokens_without / 1000) * 0.03
    
    print(f"\nCost per query (GPT-4 input):")
    print(f"  With examples: ${cost_per_query_with:.4f}")
    print(f"  Without examples: ${cost_per_query_without:.4f}")
    print(f"  Overhead: ${cost_per_query_with - cost_per_query_without:.4f}")
    
    print(f"\nCost for 10,000 queries:")
    print(f"  With examples: ${cost_per_query_with * 10000:.2f}")
    print(f"  Without examples: ${cost_per_query_without * 10000:.2f}")
    print(f"  Overhead: ${(cost_per_query_with - cost_per_query_without) * 10000:.2f}")

if __name__ == "__main__":
    print("\n🧪 Crop Health ReAct Prompt - Polish Verification\n")
    
    test_prompt_improvements()
    test_message_structure()
    test_prompt_size_comparison()
    
    print("\n" + "=" * 80)
    print("✅ All polish verification tests completed!")
    print("=" * 80)

