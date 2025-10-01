"""
Test Weather Agent Improvements (No API Key Required)

This script tests all the improvements made to the Weather Agent:
1. Configurable max_iterations
2. Dynamic examples (default disabled for token optimization)
3. Metrics tracking
4. Robust context formatting
5. Enhanced capabilities
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.weather_agent import WeatherIntelligenceAgent


def test_initialization_with_defaults():
    """Test 1: Initialization with default parameters"""
    print("\n" + "="*80)
    print("TEST 1: Initialization with Default Parameters")
    print("="*80)
    
    try:
        # Mock LLM to avoid API key requirement
        mock_llm = Mock()
        mock_llm.model_name = "gpt-4"
        
        agent = WeatherIntelligenceAgent(llm=mock_llm)
        
        print("✅ Agent initialized with defaults")
        print(f"   - Max iterations: {agent.max_iterations} (expected: 10)")
        print(f"   - Dynamic examples: {agent.enable_dynamic_examples} (expected: False for token optimization)")
        print(f"   - Metrics enabled: {agent.enable_metrics} (expected: True)")
        
        assert agent.max_iterations == 10, "Default max_iterations should be 10"
        assert agent.enable_dynamic_examples == False, "Default should be False for token optimization"
        assert agent.enable_metrics == True, "Metrics should be enabled by default"
        
        print("\n✅ All defaults correct!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configurable_parameters():
    """Test 2: Configurable parameters"""
    print("\n" + "="*80)
    print("TEST 2: Configurable Parameters")
    print("="*80)
    
    try:
        mock_llm = Mock()
        mock_llm.model_name = "gpt-4"
        
        agent = WeatherIntelligenceAgent(
            llm=mock_llm,
            max_iterations=15,
            enable_dynamic_examples=True,
            enable_metrics=False
        )
        
        print("✅ Agent initialized with custom parameters")
        print(f"   - Max iterations: {agent.max_iterations} (expected: 15)")
        print(f"   - Dynamic examples: {agent.enable_dynamic_examples} (expected: True)")
        print(f"   - Metrics enabled: {agent.enable_metrics} (expected: False)")
        
        assert agent.max_iterations == 15, "Custom max_iterations should be 15"
        assert agent.enable_dynamic_examples == True, "Should enable examples when requested"
        assert agent.enable_metrics == False, "Should disable metrics when requested"
        
        print("\n✅ All custom parameters work!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_tracking():
    """Test 3: Metrics tracking"""
    print("\n" + "="*80)
    print("TEST 3: Metrics Tracking")
    print("="*80)
    
    try:
        mock_llm = Mock()
        mock_llm.model_name = "gpt-4"
        
        agent = WeatherIntelligenceAgent(llm=mock_llm, enable_metrics=True)
        
        # Check initial metrics
        metrics = agent.get_metrics()
        print("✅ Initial metrics retrieved:")
        print(f"   - Metrics enabled: {metrics['metrics_enabled']}")
        print(f"   - Total calls: {metrics['total_calls']}")
        print(f"   - Success rate: {metrics['success_rate']}%")
        print(f"   - Avg iterations: {metrics['avg_iterations']}")
        
        assert metrics['metrics_enabled'] == True
        assert metrics['total_calls'] == 0
        assert metrics['success_rate'] == 0
        
        # Simulate some calls
        agent._update_metrics(success=True, iterations=3)
        agent._update_metrics(success=True, iterations=5)
        agent._update_metrics(success=False, error_type="validation")
        
        metrics = agent.get_metrics()
        print("\n✅ After simulated calls:")
        print(f"   - Total calls: {metrics['total_calls']} (expected: 3)")
        print(f"   - Successful: {metrics['successful_calls']} (expected: 2)")
        print(f"   - Failed: {metrics['failed_calls']} (expected: 1)")
        print(f"   - Success rate: {metrics['success_rate']}% (expected: 66.67%)")
        print(f"   - Avg iterations: {metrics['avg_iterations']} (expected: 4.0)")
        print(f"   - Error types: {metrics['error_types']}")
        
        assert metrics['total_calls'] == 3
        assert metrics['successful_calls'] == 2
        assert metrics['failed_calls'] == 1
        assert abs(metrics['success_rate'] - 66.67) < 0.1
        assert abs(metrics['avg_iterations'] - 4.0) < 0.1
        
        # Test reset
        agent.reset_metrics()
        metrics = agent.get_metrics()
        print("\n✅ After reset:")
        print(f"   - Total calls: {metrics['total_calls']} (expected: 0)")
        
        assert metrics['total_calls'] == 0
        
        print("\n✅ Metrics tracking works perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_robust_context_formatting():
    """Test 4: Robust context formatting"""
    print("\n" + "="*80)
    print("TEST 4: Robust Context Formatting")
    print("="*80)
    
    try:
        mock_llm = Mock()
        mock_llm.model_name = "gpt-4"
        
        agent = WeatherIntelligenceAgent(llm=mock_llm)
        
        # Test with standard keys
        context1 = {
            "farm_id": "FARM123",
            "location": "Beauce",
            "crop_type": "blé"
        }
        formatted1 = agent._format_context(context1)
        print("✅ Standard context:")
        print(formatted1)
        assert "Exploitation: FARM123" in formatted1
        assert "Localisation: Beauce" in formatted1
        assert "Culture: blé" in formatted1
        
        # Test with new/unknown keys (should handle dynamically)
        context2 = {
            "farm_id": "FARM456",
            "soil_type": "argileux",
            "irrigation": "goutte-à-goutte",
            "custom_field": "custom_value"
        }
        formatted2 = agent._format_context(context2)
        print("\n✅ Context with new keys (dynamic handling):")
        print(formatted2)
        assert "Exploitation: FARM456" in formatted2
        assert "Type de sol: argileux" in formatted2
        assert "Irrigation: goutte-à-goutte" in formatted2
        assert "custom_value" in formatted2  # Should handle unknown keys
        
        # Test with None values (should skip)
        context3 = {
            "farm_id": "FARM789",
            "location": None,
            "crop_type": ""
        }
        formatted3 = agent._format_context(context3)
        print("\n✅ Context with None/empty values (should skip):")
        print(formatted3)
        assert "Exploitation: FARM789" in formatted3
        assert "Localisation: None" not in formatted3  # Should skip None
        assert "Culture:" not in formatted3  # Should skip empty string
        
        # Test with empty context
        context4 = {}
        formatted4 = agent._format_context(context4)
        print("\n✅ Empty context:")
        print(f"   Result: '{formatted4}' (should be empty)")
        assert formatted4 == ""
        
        print("\n✅ Robust context formatting works perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_capabilities():
    """Test 5: Enhanced capabilities"""
    print("\n" + "="*80)
    print("TEST 5: Enhanced Capabilities")
    print("="*80)
    
    try:
        mock_llm = Mock()
        mock_llm.model_name = "gpt-4"
        
        agent = WeatherIntelligenceAgent(
            llm=mock_llm,
            max_iterations=15,
            enable_dynamic_examples=True,
            enable_metrics=True
        )
        
        capabilities = agent.get_capabilities()
        
        print("✅ Capabilities retrieved:")
        print(f"   - Agent type: {capabilities['agent_type']}")
        print(f"   - Description: {capabilities['description']}")
        print(f"   - Model: {capabilities['model']}")
        print(f"   - Max iterations: {capabilities['max_iterations']}")
        print(f"   - Dynamic examples: {capabilities['dynamic_examples_enabled']}")
        print(f"   - Metrics enabled: {capabilities['metrics_enabled']}")
        print(f"   - Number of tools: {len(capabilities['tools'])}")
        print(f"   - Number of capabilities: {len(capabilities['capabilities'])}")
        
        assert capabilities['agent_type'] == "weather_intelligence"
        assert capabilities['max_iterations'] == 15
        assert capabilities['dynamic_examples_enabled'] == True
        assert capabilities['metrics_enabled'] == True
        assert len(capabilities['tools']) == 4
        assert len(capabilities['capabilities']) >= 4
        
        print("\n   Capabilities list:")
        for cap in capabilities['capabilities']:
            print(f"   • {cap}")
        
        print("\n✅ Enhanced capabilities work perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("WEATHER AGENT IMPROVEMENTS TESTS")
    print("="*80)
    
    results = {}
    
    results['initialization_defaults'] = test_initialization_with_defaults()
    results['configurable_parameters'] = test_configurable_parameters()
    results['metrics_tracking'] = test_metrics_tracking()
    results['robust_context'] = test_robust_context_formatting()
    results['enhanced_capabilities'] = test_enhanced_capabilities()
    
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
        print("\n🎉 ALL IMPROVEMENTS VERIFIED!")
        print("\n✅ Key improvements:")
        print("   - Configurable max_iterations (default: 10 for complex reasoning)")
        print("   - Dynamic examples disabled by default (token optimization)")
        print("   - Metrics tracking with success rate and avg iterations")
        print("   - Robust context formatting (handles any keys dynamically)")
        print("   - Enhanced capabilities reporting")
    else:
        print("\n⚠️ Some tests failed. Review the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

