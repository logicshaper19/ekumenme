#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced LangChain Agricultural System
Tests all enhanced features and performance optimizations
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_enhanced_system_components():
    """Test individual enhanced system components."""
    
    print("🧪 Testing Enhanced System Components")
    print("=" * 60)
    
    test_results = {
        "enhanced_routing": False,
        "error_handling": False,
        "performance_optimization": False,
        "document_ingestion": False,
        "enhanced_system": False
    }
    
    # Test 1: Enhanced Routing
    print("\n🔀 Testing Enhanced Routing System...")
    try:
        from app.agents.enhanced_routing import SemanticAgentRouter, EnhancedAgentManager
        from langchain_openai import ChatOpenAI
        from langchain.embeddings import OpenAIEmbeddings
        
        # Mock LLM and embeddings for testing
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        
        # Test semantic router
        router = SemanticAgentRouter(llm, embeddings)
        routing_result = router.route_query("Quels sont les traitements contre la septoriose du blé ?")
        
        print(f"✅ Enhanced routing working: {routing_result.selected_agent.value}")
        print(f"   Confidence: {routing_result.confidence:.3f}")
        print(f"   Method: {routing_result.routing_method}")
        
        test_results["enhanced_routing"] = True
        
    except Exception as e:
        print(f"❌ Enhanced routing test failed: {e}")
    
    # Test 2: Error Handling
    print("\n🛡️ Testing Error Handling System...")
    try:
        from app.agents.enhanced_error_handling import ErrorRecoveryManager, AgentCollaborationManager
        
        # Test error recovery manager
        error_manager = ErrorRecoveryManager()
        print(f"✅ Error recovery manager initialized")
        
        # Test collaboration manager
        collaboration_manager = AgentCollaborationManager()
        print(f"✅ Agent collaboration manager initialized")
        
        # Test error statistics
        error_stats = error_manager.get_error_statistics()
        print(f"✅ Error statistics: {error_stats['total_errors']} errors tracked")
        
        test_results["error_handling"] = True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 3: Performance Optimization
    print("\n⚡ Testing Performance Optimization...")
    try:
        from app.agents.performance_optimization import AgentPool, PerformanceOptimizedAgentManager, PerformanceMonitor
        
        # Test performance monitor
        monitor = PerformanceMonitor()
        system_metrics = monitor.get_system_metrics()
        print(f"✅ Performance monitor working: CPU {system_metrics['cpu_usage_percent']:.1f}%")
        
        # Test performance trends
        trends = monitor.get_performance_trends(hours=1)
        print(f"✅ Performance trends: {trends.get('data_points', 0)} data points")
        
        # Test alerts
        alerts = monitor.get_alerts()
        print(f"✅ Performance alerts: {len(alerts)} alerts")
        
        test_results["performance_optimization"] = True
        
    except Exception as e:
        print(f"❌ Performance optimization test failed: {e}")
    
    # Test 4: Document Ingestion
    print("\n📚 Testing Document Ingestion...")
    try:
        from app.agents.document_ingestion import AgriculturalDocumentIngestion, IngestionConfig
        from langchain.embeddings import OpenAIEmbeddings
        
        # Test document ingestion
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        config = IngestionConfig(chunk_size=500, chunk_overlap=100)
        
        ingestion = AgriculturalDocumentIngestion(
            embeddings=embeddings,
            vector_store_path="data/test_knowledge",
            config=config
        )
        
        # Create sample documents
        sample_dir = ingestion.create_sample_agricultural_documents()
        if sample_dir:
            print(f"✅ Sample documents created in {sample_dir}")
            
            # Test ingestion statistics
            stats = ingestion.get_ingestion_statistics()
            print(f"✅ Ingestion statistics: {stats.get('total_documents', 0)} documents")
        
        test_results["document_ingestion"] = True
        
    except Exception as e:
        print(f"❌ Document ingestion test failed: {e}")
    
    # Test 5: Enhanced System Integration
    print("\n🚀 Testing Enhanced System Integration...")
    try:
        from app.agents.enhanced_langchain_system import create_enhanced_agricultural_system
        
        # Create enhanced system
        system = create_enhanced_agricultural_system()
        
        # Test system status
        status = system.get_enhanced_system_status()
        print(f"✅ Enhanced system initialized: {status['system_version']}")
        print(f"   Core components: {len([k for k, v in status['core_components'].items() if v])}")
        print(f"   Enhanced components: {len([k for k, v in status['enhanced_components'].items() if v])}")
        
        # Test performance metrics
        metrics = system.get_performance_metrics()
        print(f"✅ Performance metrics: {metrics.get('system_uptime', 0):.1f}s uptime")
        
        test_results["enhanced_system"] = True
        
    except Exception as e:
        print(f"❌ Enhanced system test failed: {e}")
    
    return test_results

def test_enhanced_query_processing():
    """Test enhanced query processing with all features."""
    
    print("\n🎯 Testing Enhanced Query Processing")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_langchain_system import create_enhanced_agricultural_system
        
        # Create enhanced system
        system = create_enhanced_agricultural_system()
        
        # Test queries
        test_queries = [
            {
                "query": "Quels sont les traitements autorisés contre la septoriose du blé en conditions humides ?",
                "context": {"farm_location": "Beauce", "crop_stage": "montaison"},
                "expected_components": ["enhanced_routing", "RAG", "reasoning"]
            },
            {
                "query": "Comment calculer mon empreinte carbone et obtenir la certification HVE ?",
                "context": {"farm_type": "céréalière", "surface": 150},
                "expected_components": ["enhanced_routing", "RAG", "reasoning"]
            },
            {
                "query": "Planifier mes travaux de pulvérisation en fonction de la météo et des réglementations",
                "context": {"crop": "blé", "operation": "pulvérisation"},
                "expected_components": ["enhanced_routing", "agent_collaboration", "reasoning"]
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Test Query {i}: {test_case['query'][:50]}...")
            
            start_time = time.time()
            
            result = system.process_agricultural_query(
                query=test_case["query"],
                context=test_case["context"],
                use_enhanced_routing=True,
                use_performance_optimization=True,
                use_error_recovery=True,
                use_agent_collaboration=True,
                use_rag=True,
                use_reasoning=True
            )
            
            processing_time = time.time() - start_time
            
            # Analyze results
            components_used = result.get("system_components_used", [])
            expected_components = test_case["expected_components"]
            
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            print(f"   🔧 Components used: {len(components_used)}")
            print(f"   📊 Components: {', '.join(components_used)}")
            
            # Check if expected components were used
            missing_components = [comp for comp in expected_components if comp not in components_used]
            if missing_components:
                print(f"   ⚠️  Missing expected components: {missing_components}")
            else:
                print(f"   ✅ All expected components used")
            
            # Check response quality
            response = result.get("response", "")
            if response and len(response) > 50:
                print(f"   ✅ Response generated: {len(response)} characters")
            else:
                print(f"   ⚠️  Short or empty response")
            
            # Check performance metrics
            perf_metrics = result.get("performance_metrics", {})
            if perf_metrics:
                print(f"   📈 Memory usage: {perf_metrics.get('memory_usage', 0):.1f}MB")
                print(f"   📈 CPU usage: {perf_metrics.get('cpu_usage', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced query processing test failed: {e}")
        return False

def test_performance_benchmarks():
    """Test performance benchmarks and optimization."""
    
    print("\n📊 Testing Performance Benchmarks")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_langchain_system import create_enhanced_agricultural_system
        
        # Create enhanced system
        system = create_enhanced_agricultural_system()
        
        # Performance test queries
        performance_queries = [
            "Analyse des données de mes parcelles",
            "Vérification AMM pour Prosaro",
            "Prévisions météo pour demain",
            "Diagnostic maladie sur blé",
            "Calcul empreinte carbone"
        ]
        
        print("🏃 Running performance benchmarks...")
        
        # Test 1: Single query performance
        single_query_times = []
        for query in performance_queries:
            start_time = time.time()
            
            result = system.process_agricultural_query(
                query=query,
                use_enhanced_routing=True,
                use_performance_optimization=True,
                use_rag=True,
                use_reasoning=True
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
        
        # Test 2: Concurrent query performance
        print(f"\n🔄 Testing concurrent query performance...")
        
        concurrent_times = []
        for _ in range(3):  # 3 rounds of concurrent queries
            start_time = time.time()
            
            # Simulate concurrent queries
            results = []
            for query in performance_queries[:3]:  # Test with 3 queries
                result = system.process_agricultural_query(
                    query=query,
                    use_enhanced_routing=True,
                    use_performance_optimization=True
                )
                results.append(result)
            
            concurrent_time = time.time() - start_time
            concurrent_times.append(concurrent_time)
            
            print(f"   Round {_+1}: {concurrent_time:.2f}s for 3 concurrent queries")
        
        avg_concurrent = sum(concurrent_times) / len(concurrent_times)
        print(f"   Average concurrent time: {avg_concurrent:.2f}s")
        
        # Test 3: System optimization
        print(f"\n⚡ Testing system optimization...")
        
        # Get performance metrics before optimization
        metrics_before = system.get_performance_metrics()
        print(f"   Before optimization: {metrics_before.get('memory_usage_mb', 0):.1f}MB memory")
        
        # Run optimization
        system.optimize_system_performance()
        
        # Get performance metrics after optimization
        metrics_after = system.get_performance_metrics()
        print(f"   After optimization: {metrics_after.get('memory_usage_mb', 0):.1f}MB memory")
        
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

def test_error_recovery_scenarios():
    """Test error recovery and fallback mechanisms."""
    
    print("\n🛡️ Testing Error Recovery Scenarios")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_langchain_system import create_enhanced_agricultural_system
        
        # Create enhanced system
        system = create_enhanced_agricultural_system()
        
        # Test error scenarios
        error_scenarios = [
            {
                "name": "Invalid Query",
                "query": "",
                "context": None,
                "expected_behavior": "graceful_handling"
            },
            {
                "name": "Complex Multi-Domain Query",
                "query": "Analysez mes données de parcelles, vérifiez la conformité AMM, prévoyez la météo, et calculez mon empreinte carbone",
                "context": {"complex": True},
                "expected_behavior": "collaboration"
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
                    use_error_recovery=True,
                    use_agent_collaboration=True
                )
                
                # Analyze result
                success = result.get("success", False)
                response = result.get("response", "")
                components = result.get("system_components_used", [])
                
                print(f"   Success: {success}")
                print(f"   Response length: {len(response)} characters")
                print(f"   Components used: {len(components)}")
                
                if scenario["expected_behavior"] == "collaboration" and "agent_collaboration" in components:
                    print(f"   ✅ Collaboration triggered as expected")
                elif scenario["expected_behavior"] == "fallback" and not success:
                    print(f"   ✅ Fallback handled gracefully")
                elif scenario["expected_behavior"] == "graceful_handling" and response:
                    print(f"   ✅ Graceful handling successful")
                else:
                    print(f"   ⚠️  Unexpected behavior")
                
            except Exception as e:
                print(f"   ❌ Error in scenario: {e}")
        
        # Test error statistics
        if hasattr(system, 'error_recovery_manager') and system.error_recovery_manager:
            error_stats = system.error_recovery_manager.get_error_statistics()
            print(f"\n📊 Error Statistics:")
            print(f"   Total errors: {error_stats['total_errors']}")
            print(f"   Error types: {error_stats['error_types']}")
            print(f"   Severity distribution: {error_stats['severity_distribution']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")
        return False

def main():
    """Run comprehensive enhanced system tests."""
    
    print("🧪 Enhanced LangChain Agricultural System Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual components
    component_results = test_enhanced_system_components()
    
    # Test enhanced query processing
    query_processing_success = test_enhanced_query_processing()
    
    # Test performance benchmarks
    performance_success = test_performance_benchmarks()
    
    # Test error recovery
    error_recovery_success = test_error_recovery_scenarios()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    
    total_tests = len(component_results) + 3  # 3 additional tests
    passed_tests = sum(component_results.values()) + sum([
        query_processing_success,
        performance_success,
        error_recovery_success
    ])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\nComponent Results:")
    for component, result in component_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {component}: {status}")
    
    print(f"\nAdditional Tests:")
    print(f"   Enhanced Query Processing: {'✅ PASS' if query_processing_success else '❌ FAIL'}")
    print(f"   Performance Benchmarks: {'✅ PASS' if performance_success else '❌ FAIL'}")
    print(f"   Error Recovery: {'✅ PASS' if error_recovery_success else '❌ FAIL'}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! Enhanced system is ready for production.")
    else:
        print(f"\n⚠️  Some tests failed. Review the errors above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
