"""
Test Orchestrator Prompt Refactoring

Verifies that the Orchestrator prompt follows the gold standard pattern.
"""

from app.prompts.orchestrator_prompts import (
    get_orchestrator_react_prompt,
    ORCHESTRATOR_CHAT_PROMPT,
    AGENT_SELECTION_PROMPT,
    RESPONSE_SYNTHESIS_PROMPT,
    CONFLICT_RESOLUTION_PROMPT,
)
from langchain_core.prompts import MessagesPlaceholder


def test_orchestrator_react_prompt():
    """Test Orchestrator ReAct prompt structure and content."""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR AGENT PROMPT REFACTORING TEST")
    print("=" * 80)
    
    # Load prompt
    prompt = get_orchestrator_react_prompt(include_examples=True)
    print("\n✅ Prompt loaded successfully")
    
    # Test 1: Message structure
    assert len(prompt.messages) == 3, f"Expected 3 messages, got {len(prompt.messages)}"
    print("✅ Correct message count: 3")
    
    # Test 2: Message types
    message_types = [type(m).__name__ for m in prompt.messages]
    expected_types = ['SystemMessagePromptTemplate', 'HumanMessagePromptTemplate', 'MessagesPlaceholder']
    assert message_types == expected_types, f"Expected {expected_types}, got {message_types}"
    print("✅ Correct message types")
    
    # Test 3: Human template is {input}
    human_template = prompt.messages[1].prompt.template
    assert human_template == "{input}", f"Expected '{{input}}', got '{human_template}'"
    print("✅ Correct human template: {input}")
    
    # Test 4: MessagesPlaceholder for agent_scratchpad
    scratchpad = prompt.messages[2]
    assert isinstance(scratchpad, MessagesPlaceholder), "Third message should be MessagesPlaceholder"
    assert scratchpad.variable_name == "agent_scratchpad", f"Expected 'agent_scratchpad', got '{scratchpad.variable_name}'"
    print("✅ Correct MessagesPlaceholder: agent_scratchpad")
    
    # Test 5: System prompt content
    system_template = prompt.messages[0].prompt.template
    
    # Check for critical sections
    critical_sections = [
        "OUTILS DISPONIBLES",
        "FORMAT DE RAISONNEMENT ReAct",
        "EXEMPLE CONCRET D'ORCHESTRATION MULTI-AGENTS",
        "RÈGLES CRITIQUES",
        "GESTION DES RAISONNEMENTS LONGS",
    ]
    
    for section in critical_sections:
        assert section in system_template, f"Missing section: {section}"
        print(f"✅ {section}")
    
    # Test 6: Critical rules present
    critical_rules = [
        "N'invente JAMAIS \"Observation:\"",
        "Action Input doit TOUJOURS être un JSON valide",
        "le système le génère automatiquement",
        "Ne réponds JAMAIS sans consulter les agents spécialisés",
        "Consulte 1 à 3 agents maximum",
    ]
    
    for rule in critical_rules:
        assert rule in system_template, f"Missing critical rule: {rule}"
        print(f"✅ Critical rule: {rule}...")
    
    # Test 7: Concrete example present
    assert "delegate_to_agent" in system_template, "Missing delegate_to_agent in example"
    assert "Puis-je traiter mes tomates contre le mildiou" in system_template, "Missing concrete example question"
    assert "Thought:" in system_template and "Action:" in system_template, "Missing ReAct format keywords"
    print("✅ Concrete multi-agent orchestration example present")
    
    # Test 8: Agent list present
    agents = [
        "Farm Data Agent",
        "Regulatory Agent",
        "Weather Agent",
        "Crop Health Agent",
        "Planning Agent",
        "Sustainability Agent",
    ]
    
    for agent in agents:
        assert agent in system_template, f"Missing agent: {agent}"
    print("✅ All 6 specialized agents listed")
    
    # Test 9: Routing rules present
    routing_rules = [
        "Produits/Traitements",
        "Timing d'intervention",
        "Analyse de parcelles",
        "Planification",
        "Problèmes phytosanitaires",
        "Questions de durabilité",
    ]
    
    for rule in routing_rules:
        assert rule in system_template, f"Missing routing rule: {rule}"
    print("✅ All routing rules present")
    
    # Calculate prompt size
    prompt_size = len(system_template)
    estimated_tokens = prompt_size // 4
    print(f"\n📊 Prompt size: {prompt_size:,} characters (~{estimated_tokens:,} tokens)")
    
    print("\n" + "=" * 80)
    print("✅ ORCHESTRATOR AGENT: ALL TESTS PASSED")
    print("=" * 80)
    
    return True


def test_non_react_prompts():
    """Test non-ReAct conversational prompts."""
    print("\n" + "=" * 80)
    print("NON-REACT PROMPTS TEST")
    print("=" * 80)
    
    # Test chat prompt
    assert len(ORCHESTRATOR_CHAT_PROMPT.messages) == 2, "Chat prompt should have 2 messages"
    print("✅ ORCHESTRATOR_CHAT_PROMPT: 2 messages (system, human)")
    
    # Test selection prompt
    assert len(AGENT_SELECTION_PROMPT.messages) == 2, "Selection prompt should have 2 messages"
    print("✅ AGENT_SELECTION_PROMPT: 2 messages (system, human)")
    
    # Test synthesis prompt
    assert len(RESPONSE_SYNTHESIS_PROMPT.messages) == 2, "Synthesis prompt should have 2 messages"
    print("✅ RESPONSE_SYNTHESIS_PROMPT: 2 messages (system, human)")
    
    # Test conflict resolution prompt
    assert len(CONFLICT_RESOLUTION_PROMPT.messages) == 2, "Conflict prompt should have 2 messages"
    print("✅ CONFLICT_RESOLUTION_PROMPT: 2 messages (system, human)")
    
    print("\n" + "=" * 80)
    print("✅ NON-REACT PROMPTS: ALL TESTS PASSED")
    print("=" * 80)
    
    return True


def test_orchestrator_example_quality():
    """Test the quality of the concrete example."""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR EXAMPLE QUALITY TEST")
    print("=" * 80)
    
    prompt = get_orchestrator_react_prompt(include_examples=True)
    system_template = prompt.messages[0].prompt.template
    
    # Check for multi-step reasoning (should have multiple Thought/Action cycles)
    thought_count = system_template.count("Thought:")
    action_count = system_template.count("Action:")
    
    assert thought_count >= 4, f"Expected at least 4 Thoughts in example, got {thought_count}"
    assert action_count >= 3, f"Expected at least 3 Actions in example, got {action_count}"
    print(f"✅ Multi-step example: {thought_count} thoughts, {action_count} actions")
    
    # Check for proper agent delegation
    assert "weather" in system_template, "Example should delegate to weather agent"
    assert "crop_health" in system_template, "Example should delegate to crop_health agent"
    assert "regulatory" in system_template, "Example should delegate to regulatory agent"
    print("✅ Example delegates to multiple agents (weather, crop_health, regulatory)")
    
    # Check for synthesis in Final Answer
    assert "Final Answer:" in system_template, "Example should have Final Answer"
    assert "**Diagnostic:**" in system_template or "**Fenêtre d'intervention" in system_template, "Final Answer should be structured"
    print("✅ Example includes structured Final Answer with synthesis")
    
    # Check for realistic agricultural scenario
    assert "mildiou" in system_template or "tomates" in system_template, "Example should use realistic agricultural scenario"
    assert "AMM" in system_template or "dose" in system_template or "DAR" in system_template, "Example should include regulatory details"
    print("✅ Example uses realistic agricultural scenario with regulatory compliance")
    
    print("\n" + "=" * 80)
    print("✅ ORCHESTRATOR EXAMPLE QUALITY: ALL TESTS PASSED")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    print("\n🧪 Orchestrator Prompt Refactoring Test\n")
    
    try:
        test_orchestrator_react_prompt()
        test_non_react_prompts()
        test_orchestrator_example_quality()
        
        print("\n" + "=" * 80)
        print("🎉 ALL ORCHESTRATOR TESTS PASSED!")
        print("=" * 80)
        print("\n✅ Orchestrator prompt is production-ready and follows gold standard pattern")
        print("✅ All critical sections present")
        print("✅ Proper ReAct format")
        print("✅ MessagesPlaceholder configured correctly")
        print("✅ Multi-agent orchestration example included")
        print("✅ All routing rules and agents documented")
        print("\n🚀 Ready for deployment!\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise

