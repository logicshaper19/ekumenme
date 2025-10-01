#!/usr/bin/env python3
"""
Test script for the integrated orchestrator system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.orchestration import (
    create_complete_integrated_orchestrator,
    validate_system_integration,
    AgentType,
    TaskComplexity,
    TaskComplexityAnalyzer
)

def test_basic_functionality():
    """Test basic orchestrator functionality."""
    print("🧪 Testing Integrated Orchestrator...")
    
    try:
        # Create orchestrator
        orchestrator = create_complete_integrated_orchestrator()
        print("✅ Orchestrator created successfully")
        
        # Test system status
        status = orchestrator.get_system_status()
        print(f"✅ System status: {status['orchestrator_status']}")
        
        # Test agent selection
        test_queries = [
            "Quelle est la météo aujourd'hui?",
            "Ce produit est-il autorisé sur blé?",
            "Analyse les rendements de mes parcelles",
            "Comment traiter la septoriose?"
        ]
        
        for query in test_queries:
            debug_info = orchestrator.debug_agent_selection(query)
            print(f"✅ Query: '{query}' -> Agent: {debug_info.get('selected_agent', 'Unknown')}")
        
        # Test knowledge retrieval
        knowledge_debug = orchestrator.debug_knowledge_retrieval("septoriose blé")
        print(f"✅ Knowledge retrieval: {knowledge_debug.get('knowledge_count', 0)} chunks found")
        
        # Test cost analysis
        cost_analysis = orchestrator.get_cost_analysis()
        print(f"✅ Cost optimization: {cost_analysis.get('cost_optimization_active', False)}")
        
        # Validate system integration
        validation = validate_system_integration(orchestrator)
        print(f"✅ Integration score: {validation['integration_summary']['overall_score']}%")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complexity_analysis():
    """Test task complexity analysis."""
    print("\n🧪 Testing Task Complexity Analysis...")
    
    test_cases = [
        ("Quelle est la température?", TaskComplexity.SIMPLE),
        ("Analyse les données de rendement", TaskComplexity.MODERATE),
        ("Optimise la rentabilité de l'exploitation", TaskComplexity.COMPLEX),
        ("Vérifier l'AMM de ce produit", TaskComplexity.CRITICAL),
    ]
    
    for query, expected in test_cases:
        result = TaskComplexityAnalyzer.analyze_complexity(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{query}' -> {result.value} (expected: {expected.value})")
    
    return True

def test_agent_types():
    """Test agent type enumeration."""
    print("\n🧪 Testing Agent Types...")
    
    expected_agents = [
        "farm_data_manager",
        "regulatory_compliance", 
        "weather_intelligence",
        "crop_health",
        "operational_economic_planning",
        "sustainability_analytics"
    ]
    
    actual_agents = [agent.value for agent in AgentType]
    
    for expected in expected_agents:
        if expected in actual_agents:
            print(f"✅ Agent type '{expected}' found")
        else:
            print(f"❌ Agent type '{expected}' missing")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Integrated Orchestrator Tests\n")
    
    tests = [
        test_basic_functionality,
        test_complexity_analysis,
        test_agent_types
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The integrated orchestrator is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)
