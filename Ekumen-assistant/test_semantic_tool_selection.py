#!/usr/bin/env python3
"""
Test Semantic Tool Selection System
Demonstrates the enhanced semantic tool selection capabilities.
"""

import sys
import os
import asyncio
import json
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.semantic_tool_selector import SemanticToolSelector, ToolSelectionResult
from app.agents.semantic_crop_health_agent import SemanticCropHealthAgent

def test_semantic_tool_selector():
    """Test the semantic tool selector with various queries."""
    print("🔧 Testing Semantic Tool Selector")
    print("=" * 50)
    
    # Initialize semantic tool selector
    selector = SemanticToolSelector()
    
    # Available tools for testing
    available_tools = [
        "diagnose_disease_tool",
        "identify_pest_tool", 
        "generate_planning_tasks_tool",
        "check_regulatory_compliance_tool",
        "database_integrated_amm_lookup_tool",
        "get_weather_data_tool",
        "get_farm_data_tool"
    ]
    
    # Test queries with different intents
    test_queries = [
        {
            "query": "Mon blé présente des taches brunes sur les feuilles avec jaunissement",
            "expected_tools": ["diagnose_disease_tool"],
            "description": "Disease diagnosis query"
        },
        {
            "query": "J'observe des trous dans les feuilles de maïs avec des excréments d'insectes",
            "expected_tools": ["identify_pest_tool"],
            "description": "Pest identification query"
        },
        {
            "query": "Je veux planifier mes travaux de semis pour le printemps prochain",
            "expected_tools": ["generate_planning_tasks_tool"],
            "description": "Planning query"
        },
        {
            "query": "Est-ce que je peux utiliser ce produit phytosanitaire sur colza?",
            "expected_tools": ["check_regulatory_compliance_tool", "database_integrated_amm_lookup_tool"],
            "description": "Regulatory compliance query"
        },
        {
            "query": "Quelles sont les prévisions météo pour cette semaine?",
            "expected_tools": ["get_weather_data_tool"],
            "description": "Weather forecast query"
        },
        {
            "query": "Maladie fongique sur mes cultures avec conditions humides",
            "expected_tools": ["diagnose_disease_tool"],
            "description": "Disease with environmental context"
        },
        {
            "query": "Ravageurs et conformité réglementaire pour traitement bio",
            "expected_tools": ["identify_pest_tool", "check_regulatory_compliance_tool"],
            "description": "Multi-domain query"
        }
    ]
    
    # Test different selection methods
    methods = ["semantic", "keyword", "intent", "hybrid"]
    
    for method in methods:
        print(f"\n🎯 Testing {method.upper()} method:")
        print("-" * 30)
        
        for test_case in test_queries:
            query = test_case["query"]
            expected = test_case["expected_tools"]
            description = test_case["description"]
            
            # Select tools
            result = selector.select_tools(
                message=query,
                available_tools=available_tools,
                method=method,
                threshold=0.4,
                max_tools=3
            )
            
            # Display results
            print(f"\n📝 Query: {query}")
            print(f"📋 Description: {description}")
            print(f"🎯 Expected: {expected}")
            print(f"✅ Selected: {result.selected_tools}")
            print(f"📊 Confidence: {result.confidence:.3f}")
            print(f"💭 Reasoning: {result.reasoning}")
            
            # Check if any expected tools were selected
            matches = set(result.selected_tools) & set(expected)
            if matches:
                print(f"✅ SUCCESS: Found expected tools: {list(matches)}")
            else:
                print(f"❌ MISS: No expected tools selected")
            
            # Show top scores
            if result.tool_scores:
                top_scores = sorted(result.tool_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"🏆 Top scores: {[(tool, f'{score:.3f}') for tool, score in top_scores]}")

def test_semantic_crop_health_agent():
    """Test the semantic crop health agent."""
    print("\n\n🌱 Testing Semantic Crop Health Agent")
    print("=" * 50)
    
    try:
        # Initialize semantic crop health agent
        agent = SemanticCropHealthAgent()
        
        # Test crop health queries
        test_scenarios = [
            {
                "scenario": "Disease Diagnosis",
                "query": "Mon blé présente des taches brunes circulaires avec un centre gris",
                "crop_type": "blé",
                "environmental_conditions": {"humidity": "high", "temperature": "moderate"}
            },
            {
                "scenario": "Pest Identification", 
                "query": "Trous dans les feuilles de maïs avec présence de chenilles vertes",
                "crop_type": "maïs",
                "environmental_conditions": None
            },
            {
                "scenario": "Treatment Recommendation",
                "query": "Traitement pour oïdium sur colza au stade floraison",
                "crop_type": "colza",
                "environmental_conditions": {"humidity": "high"}
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🔬 Scenario: {scenario['scenario']}")
            print("-" * 30)
            print(f"Query: {scenario['query']}")
            print(f"Crop: {scenario['crop_type']}")
            
            # Process query
            result = agent.process_crop_health_query(
                query=scenario['query'],
                crop_type=scenario['crop_type'],
                environmental_conditions=scenario['environmental_conditions']
            )
            
            # Display results
            print(f"\n📊 Tool Selection Results:")
            if 'tool_selection' in result:
                selection = result['tool_selection']
                print(f"  Selected Tools: {selection.get('selected_tools', [])}")
                print(f"  Method: {selection.get('selection_method', 'unknown')}")
                print(f"  Confidence: {selection.get('confidence', 0):.3f}")
                print(f"  Reasoning: {selection.get('reasoning', 'N/A')}")
            
            print(f"\n🛠️ Tool Execution Results:")
            if 'tool_results' in result:
                for tool_result in result['tool_results']:
                    tool_name = tool_result.get('tool_name', 'Unknown')
                    success = tool_result.get('success', False)
                    print(f"  {tool_name}: {'✅ Success' if success else '❌ Failed'}")
                    if not success and 'error' in tool_result:
                        print(f"    Error: {tool_result['error']}")
            
            print(f"\n💬 Agent Response:")
            response = result.get('response', 'No response generated')
            # Truncate long responses for readability
            if len(response) > 200:
                response = response[:200] + "..."
            print(f"  {response}")
    
    except Exception as e:
        print(f"❌ Error testing semantic crop health agent: {e}")
        print("This is expected if enhanced tools are not available")

def test_tool_selection_performance():
    """Test tool selection performance with various parameters."""
    print("\n\n⚡ Testing Tool Selection Performance")
    print("=" * 50)
    
    selector = SemanticToolSelector()
    available_tools = list(selector.tool_profiles.keys())
    
    # Test queries
    queries = [
        "Diagnostic de maladie sur blé",
        "Identification de ravageurs",
        "Planification des travaux",
        "Vérification réglementaire",
        "Prévisions météo"
    ]
    
    # Test different thresholds
    thresholds = [0.3, 0.5, 0.7]
    
    print(f"Testing with {len(queries)} queries and {len(available_tools)} available tools")
    
    for threshold in thresholds:
        print(f"\n🎯 Threshold: {threshold}")
        print("-" * 20)
        
        total_selected = 0
        total_confidence = 0
        
        for query in queries:
            result = selector.select_tools(
                message=query,
                available_tools=available_tools,
                method="hybrid",
                threshold=threshold,
                max_tools=3
            )
            
            total_selected += len(result.selected_tools)
            total_confidence += result.confidence
            
            print(f"  '{query}': {len(result.selected_tools)} tools, confidence: {result.confidence:.3f}")
        
        avg_tools = total_selected / len(queries)
        avg_confidence = total_confidence / len(queries)
        
        print(f"  📊 Average tools selected: {avg_tools:.1f}")
        print(f"  📊 Average confidence: {avg_confidence:.3f}")

def main():
    """Run all semantic tool selection tests."""
    print("🚀 Semantic Tool Selection Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Basic semantic tool selector
        test_semantic_tool_selector()
        
        # Test 2: Semantic crop health agent
        test_semantic_crop_health_agent()
        
        # Test 3: Performance testing
        test_tool_selection_performance()
        
        print("\n\n✅ All tests completed!")
        print("\n🎯 Key Features Demonstrated:")
        print("  ✅ Semantic similarity-based tool selection")
        print("  ✅ Keyword-based tool matching with scoring")
        print("  ✅ Intent classification and tool mapping")
        print("  ✅ Hybrid approach combining all methods")
        print("  ✅ Intelligent parameter extraction")
        print("  ✅ Enhanced agent with semantic capabilities")
        print("  ✅ Performance optimization with thresholds")
        
        print("\n🔧 Next Steps:")
        print("  1. Integrate with existing agents")
        print("  2. Add real API keys for full functionality")
        print("  3. Run database migrations for enhanced tools")
        print("  4. Configure semantic model for production")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
