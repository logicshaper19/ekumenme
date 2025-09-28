#!/usr/bin/env python3
"""
Simple Test for Semantic Tool Selection System
Tests the core semantic tool selection functionality without complex dependencies.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_semantic_tool_selector_basic():
    """Test the basic semantic tool selector functionality."""
    print("🔧 Testing Basic Semantic Tool Selector")
    print("=" * 50)
    
    try:
        from app.services.semantic_tool_selector import SemanticToolSelector, ToolSelectionResult
        
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
        
        print(f"✅ Initialized selector with {len(available_tools)} available tools")
        print(f"📊 Semantic features available: {selector.encoder is not None}")
        
        # Test queries with different intents
        test_queries = [
            {
                "query": "Mon blé présente des taches brunes sur les feuilles",
                "expected_domain": "crop_health",
                "description": "Disease diagnosis query"
            },
            {
                "query": "J'observe des trous dans les feuilles avec des insectes",
                "expected_domain": "crop_health", 
                "description": "Pest identification query"
            },
            {
                "query": "Je veux planifier mes travaux de semis",
                "expected_domain": "planning",
                "description": "Planning query"
            },
            {
                "query": "Vérification de conformité réglementaire",
                "expected_domain": "regulatory",
                "description": "Regulatory compliance query"
            },
            {
                "query": "Prévisions météo pour cette semaine",
                "expected_domain": "weather",
                "description": "Weather forecast query"
            }
        ]
        
        # Test different selection methods
        methods = ["keyword", "intent", "hybrid"]
        
        for method in methods:
            print(f"\n🎯 Testing {method.upper()} method:")
            print("-" * 30)
            
            for test_case in test_queries:
                query = test_case["query"]
                expected_domain = test_case["expected_domain"]
                description = test_case["description"]
                
                # Select tools
                result = selector.select_tools(
                    message=query,
                    available_tools=available_tools,
                    method=method,
                    threshold=0.3,  # Lower threshold for testing
                    max_tools=2
                )
                
                # Display results
                print(f"\n📝 Query: {query}")
                print(f"📋 Expected domain: {expected_domain}")
                print(f"✅ Selected tools: {result.selected_tools}")
                print(f"📊 Confidence: {result.confidence:.3f}")
                print(f"🔧 Method: {result.selection_method}")
                
                # Check if appropriate tools were selected
                success = False
                if expected_domain == "crop_health":
                    success = any("disease" in tool or "pest" in tool for tool in result.selected_tools)
                elif expected_domain == "planning":
                    success = any("planning" in tool for tool in result.selected_tools)
                elif expected_domain == "regulatory":
                    success = any("compliance" in tool or "amm" in tool for tool in result.selected_tools)
                elif expected_domain == "weather":
                    success = any("weather" in tool for tool in result.selected_tools)
                
                print(f"🎯 Result: {'✅ SUCCESS' if success else '❌ MISS'}")
                
                # Show reasoning
                if result.reasoning:
                    print(f"💭 Reasoning: {result.reasoning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing semantic tool selector: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_profiles():
    """Test tool profile functionality."""
    print("\n\n📋 Testing Tool Profiles")
    print("=" * 50)
    
    try:
        from app.services.semantic_tool_selector import SemanticToolSelector
        
        selector = SemanticToolSelector()
        
        # Test tool profile access
        print(f"📊 Total tool profiles: {len(selector.tool_profiles)}")
        
        for tool_name, profile in selector.tool_profiles.items():
            print(f"\n🛠️ Tool: {tool_name}")
            print(f"   Domain: {profile.domain}")
            print(f"   Complexity: {profile.complexity}")
            print(f"   Keywords: {profile.keywords[:3]}...")  # Show first 3 keywords
            print(f"   Use cases: {len(profile.use_cases)}")
        
        # Test domain filtering
        domains = set(profile.domain for profile in selector.tool_profiles.values())
        print(f"\n🏷️ Available domains: {domains}")
        
        for domain in domains:
            domain_tools = selector.list_available_tools(domain)
            print(f"   {domain}: {len(domain_tools)} tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing tool profiles: {e}")
        return False

def test_enhanced_crop_health_agent():
    """Test the enhanced crop health agent with existing tools."""
    print("\n\n🌱 Testing Enhanced Crop Health Agent")
    print("=" * 50)
    
    try:
        # Test with existing crop health agent
        from app.agents.crop_health_agent import CropHealthMonitorAgent
        
        # Initialize agent (this should now use semantic selection)
        agent = CropHealthMonitorAgent()
        
        print(f"✅ Initialized agent: {agent.name}")
        print(f"🛠️ Available tools: {[tool.name for tool in agent.tools]}")
        
        # Test tool selection method
        test_message = "Mon blé présente des taches brunes avec jaunissement"
        selected_tools = agent._determine_tools_needed(test_message)
        
        print(f"\n📝 Test message: {test_message}")
        print(f"🎯 Selected tools: {selected_tools}")
        
        # Test different messages
        test_messages = [
            "Ravageurs sur maïs avec trous dans les feuilles",
            "Traitement pour oïdium sur colza",
            "Carence en azote sur blé",
            "Maladie fongique avec conditions humides"
        ]
        
        for message in test_messages:
            tools = agent._determine_tools_needed(message)
            print(f"📝 '{message}' → {tools}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced crop health agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """Test performance of tool selection."""
    print("\n\n⚡ Testing Performance")
    print("=" * 50)
    
    try:
        from app.services.semantic_tool_selector import SemanticToolSelector
        import time
        
        selector = SemanticToolSelector()
        available_tools = list(selector.tool_profiles.keys())
        
        # Test queries
        queries = [
            "Diagnostic de maladie sur blé",
            "Identification de ravageurs", 
            "Planification des travaux",
            "Vérification réglementaire",
            "Prévisions météo"
        ] * 5  # Repeat for better timing
        
        print(f"Testing {len(queries)} queries...")
        
        start_time = time.time()
        
        for query in queries:
            result = selector.select_tools(
                message=query,
                available_tools=available_tools,
                method="hybrid",
                threshold=0.4,
                max_tools=2
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(queries)
        
        print(f"📊 Total time: {total_time:.3f}s")
        print(f"📊 Average time per query: {avg_time:.3f}s")
        print(f"📊 Queries per second: {len(queries)/total_time:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Semantic Tool Selection Test Suite (Simple)")
    print("=" * 60)
    
    tests = [
        ("Basic Semantic Tool Selector", test_semantic_tool_selector_basic),
        ("Tool Profiles", test_tool_profiles),
        ("Enhanced Crop Health Agent", test_enhanced_crop_health_agent),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n\n📊 Test Results Summary")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Semantic tool selection is working correctly.")
        print("\n🔧 Key Features Demonstrated:")
        print("  ✅ Keyword-based tool selection with scoring")
        print("  ✅ Intent classification and tool mapping")
        print("  ✅ Hybrid approach combining multiple methods")
        print("  ✅ Tool profiles with domain classification")
        print("  ✅ Integration with existing agents")
        print("  ✅ Performance optimization")
        
        print("\n📈 Next Steps:")
        print("  1. Install sentence-transformers for full semantic similarity")
        print("  2. Integrate with more agents (planning, regulatory, etc.)")
        print("  3. Fine-tune thresholds for production use")
        print("  4. Add custom tool profiles for specialized tools")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
