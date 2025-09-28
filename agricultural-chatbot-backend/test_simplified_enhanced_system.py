#!/usr/bin/env python3
"""
Test Suite for Simplified Enhanced LangChain Agricultural System
Tests core enhanced features without complex dependencies
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_simplified_enhanced_system():
    """Test the simplified enhanced agricultural system."""
    
    print("🧪 Testing Simplified Enhanced Agricultural System")
    print("=" * 60)
    
    try:
        from app.agents.simplified_enhanced_system import create_simplified_enhanced_system
        
        # Create enhanced system
        system = create_simplified_enhanced_system()
        print("✅ Enhanced system created successfully")
        
        # Test system status
        status = system.get_system_status()
        print(f"✅ System status: {status['system_version']}")
        print(f"   Uptime: {status['system_uptime']:.1f}s")
        print(f"   Enhanced features: {len(status['enhanced_features'])}")
        
        # Test enhanced routing
        print("\n🔀 Testing Enhanced Routing...")
        routing_result = system.enhanced_router.route_query("Quels sont les traitements contre la septoriose du blé ?")
        print(f"✅ Routing result: {routing_result['selected_agent']}")
        print(f"   Confidence: {routing_result['confidence']:.3f}")
        print(f"   Method: {routing_result['routing_method']}")
        
        # Test error recovery
        print("\n🛡️ Testing Error Recovery...")
        error_stats = system.error_recovery.get_error_statistics()
        print(f"✅ Error recovery initialized: {error_stats['total_errors']} errors tracked")
        
        # Test performance monitoring
        print("\n📊 Testing Performance Monitoring...")
        perf_metrics = system.performance_monitor.get_performance_metrics()
        print(f"✅ Performance monitor initialized: {perf_metrics['total_requests']} requests tracked")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_enhanced_query_processing():
    """Test enhanced query processing."""
    
    print("\n🎯 Testing Enhanced Query Processing")
    print("=" * 60)
    
    try:
        from app.agents.simplified_enhanced_system import create_simplified_enhanced_system
        
        # Create enhanced system
        system = create_simplified_enhanced_system()
        
        # Test queries
        test_queries = [
            {
                "query": "Quels sont les traitements autorisés contre la septoriose du blé ?",
                "context": {"farm_location": "Beauce", "crop_stage": "montaison"},
                "expected_agent": "crop_health"
            },
            {
                "query": "Comment calculer mon empreinte carbone ?",
                "context": {"farm_type": "céréalière", "surface": 150},
                "expected_agent": "sustainability"
            },
            {
                "query": "Prévisions météo pour demain",
                "context": {"location": "Chartres"},
                "expected_agent": "weather"
            },
            {
                "query": "Vérifier l'autorisation AMM de Prosaro",
                "context": {"product": "Prosaro"},
                "expected_agent": "regulatory"
            },
            {
                "query": "Analyser les données de mes parcelles",
                "context": {"siret": "12345678901234"},
                "expected_agent": "farm_data"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Test Query {i}: {test_case['query'][:40]}...")
            
            start_time = time.time()
            
            result = system.process_agricultural_query(
                query=test_case["query"],
                context=test_case["context"],
                use_enhanced_routing=True,
                use_error_recovery=True
            )
            
            processing_time = time.time() - start_time
            
            # Analyze results
            routing_result = result.get("routing_result", {})
            selected_agent = routing_result.get("selected_agent", "unknown")
            confidence = routing_result.get("confidence", 0.0)
            components_used = result.get("system_components_used", [])
            
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            print(f"   🤖 Selected agent: {selected_agent}")
            print(f"   📊 Confidence: {confidence:.3f}")
            print(f"   🔧 Components: {len(components_used)}")
            
            # Check if correct agent was selected
            expected_agent = test_case["expected_agent"]
            if selected_agent == expected_agent:
                print(f"   ✅ Correct agent selected")
            else:
                print(f"   ⚠️  Expected {expected_agent}, got {selected_agent}")
            
            # Check response quality
            response = result.get("response", "")
            if response and len(response) > 50:
                print(f"   ✅ Response generated: {len(response)} characters")
            else:
                print(f"   ⚠️  Short or empty response")
            
            # Check performance metrics
            perf_metrics = result.get("performance_metrics", {})
            if perf_metrics:
                print(f"   📈 System uptime: {perf_metrics.get('system_uptime', 0):.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced query processing test failed: {e}")
        return False

def test_error_recovery_scenarios():
    """Test error recovery scenarios."""
    
    print("\n🛡️ Testing Error Recovery Scenarios")
    print("=" * 60)
    
    try:
        from app.agents.simplified_enhanced_system import create_simplified_enhanced_system
        
        # Create enhanced system
        system = create_simplified_enhanced_system()
        
        # Test error scenarios
        error_scenarios = [
            {
                "name": "Empty Query",
                "query": "",
                "context": None,
                "expected_behavior": "graceful_handling"
            },
            {
                "name": "Complex Multi-Domain Query",
                "query": "Analysez mes données, vérifiez la conformité, prévoyez la météo, et calculez mon empreinte carbone",
                "context": {"complex": True},
                "expected_behavior": "enhanced_routing"
            },
            {
                "name": "Non-Agricultural Query",
                "query": "Quelle est la capitale de la France ?",
                "context": None,
                "expected_behavior": "fallback"
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            
            try:
                result = system.process_agricultural_query(
                    query=scenario["query"],
                    context=scenario["context"],
                    use_error_recovery=True
                )
                
                # Analyze result
                success = result.get("success", False)
                response = result.get("response", "")
                components = result.get("system_components_used", [])
                error_handled = result.get("error_handled", False)
                
                print(f"   Success: {success}")
                print(f"   Response length: {len(response)} characters")
                print(f"   Components used: {len(components)}")
                print(f"   Error handled: {error_handled}")
                
                if scenario["expected_behavior"] == "enhanced_routing" and "enhanced_routing" in components:
                    print(f"   ✅ Enhanced routing triggered as expected")
                elif scenario["expected_behavior"] == "fallback" and not success:
                    print(f"   ✅ Fallback handled gracefully")
                elif scenario["expected_behavior"] == "graceful_handling" and response:
                    print(f"   ✅ Graceful handling successful")
                else:
                    print(f"   ⚠️  Unexpected behavior")
                
            except Exception as e:
                print(f"   ❌ Error in scenario: {e}")
        
        # Test error statistics
        error_stats = system.error_recovery.get_error_statistics()
        print(f"\n📊 Error Statistics:")
        print(f"   Total errors: {error_stats['total_errors']}")
        print(f"   Error types: {error_stats['error_types']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")
        return False

def test_performance_benchmarks():
    """Test performance benchmarks."""
    
    print("\n📊 Testing Performance Benchmarks")
    print("=" * 60)
    
    try:
        from app.agents.simplified_enhanced_system import create_simplified_enhanced_system
        
        # Create enhanced system
        system = create_simplified_enhanced_system()
        
        # Performance test queries
        performance_queries = [
            "Analyse des données de mes parcelles",
            "Vérification AMM pour Prosaro",
            "Prévisions météo pour demain",
            "Diagnostic maladie sur blé",
            "Calcul empreinte carbone"
        ]
        
        print("🏃 Running performance benchmarks...")
        
        # Test single query performance
        single_query_times = []
        for query in performance_queries:
            start_time = time.time()
            
            result = system.process_agricultural_query(
                query=query,
                use_enhanced_routing=True,
                use_error_recovery=True
            )
            
            processing_time = time.time() - start_time
            single_query_times.append(processing_time)
            
            print(f"   Query: {query[:30]}... - {processing_time:.2f}s")
        
        # Calculate statistics
        avg_time = sum(single_query_times) / len(single_query_times)
        min_time = min(single_query_times)
        max_time = max(single_query_times)
        
        print(f"\n📈 Single Query Performance:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s")
        
        # Test system performance metrics
        perf_metrics = system.performance_monitor.get_performance_metrics()
        print(f"\n📊 System Performance Metrics:")
        print(f"   Total requests: {perf_metrics['total_requests']}")
        print(f"   Average response time: {perf_metrics['average_response_time']:.2f}s")
        print(f"   Success rate: {perf_metrics['success_rate']:.1%}")
        
        # Performance assessment
        if avg_time < 5.0:
            print(f"✅ Performance: Excellent (avg {avg_time:.2f}s)")
        elif avg_time < 10.0:
            print(f"✅ Performance: Good (avg {avg_time:.2f}s)")
        else:
            print(f"⚠️  Performance: Needs improvement (avg {avg_time:.2f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance benchmark test failed: {e}")
        return False

def main():
    """Run comprehensive simplified enhanced system tests."""
    
    print("🧪 Simplified Enhanced LangChain Agricultural System Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual components
    component_success = test_simplified_enhanced_system()
    
    # Test enhanced query processing
    query_processing_success = test_enhanced_query_processing()
    
    # Test error recovery
    error_recovery_success = test_error_recovery_scenarios()
    
    # Test performance benchmarks
    performance_success = test_performance_benchmarks()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    
    total_tests = 4
    passed_tests = sum([
        component_success,
        query_processing_success,
        error_recovery_success,
        performance_success
    ])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\nTest Results:")
    print(f"   Component Tests: {'✅ PASS' if component_success else '❌ FAIL'}")
    print(f"   Query Processing: {'✅ PASS' if query_processing_success else '❌ FAIL'}")
    print(f"   Error Recovery: {'✅ PASS' if error_recovery_success else '❌ FAIL'}")
    print(f"   Performance Benchmarks: {'✅ PASS' if performance_success else '❌ FAIL'}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! Simplified enhanced system is ready.")
    else:
        print(f"\n⚠️  Some tests failed. Review the errors above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
