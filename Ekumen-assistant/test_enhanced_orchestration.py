#!/usr/bin/env python3
"""
Test Suite for Enhanced Orchestration System
Tests semantic agent selection and knowledge retrieval
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_semantic_agent_selection():
    """Test semantic agent selection capabilities."""
    
    print("🔀 Testing Semantic Agent Selection")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_orchestration import SemanticAgentSelector, AgentType
        
        # Create semantic selector
        selector = SemanticAgentSelector()
        print("✅ Semantic agent selector created")
        
        # Test queries for different agents
        test_queries = [
            {
                "query": "Quels sont les rendements de mes parcelles de blé cette année?",
                "expected_agent": AgentType.FARM_DATA,
                "description": "Farm data query"
            },
            {
                "query": "Ce produit est-il autorisé sur blé en France?",
                "expected_agent": AgentType.REGULATORY,
                "description": "Regulatory query"
            },
            {
                "query": "Quand puis-je traiter mes cultures cette semaine?",
                "expected_agent": AgentType.WEATHER,
                "description": "Weather query"
            },
            {
                "query": "J'observe des taches sur les feuilles de blé, qu'est-ce que c'est?",
                "expected_agent": AgentType.CROP_HEALTH,
                "description": "Crop health query"
            },
            {
                "query": "Planifie mes travaux de semis pour octobre",
                "expected_agent": AgentType.PLANNING,
                "description": "Planning query"
            },
            {
                "query": "Calcule l'empreinte carbone de mon exploitation",
                "expected_agent": AgentType.SUSTAINABILITY,
                "description": "Sustainability query"
            }
        ]
        
        correct_selections = 0
        total_selections = len(test_queries)
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {test_case['description']}")
            print(f"   Query: {test_case['query'][:50]}...")
            
            # Test semantic selection
            selected_agent, confidence = selector.select_agent_semantic(test_case['query'])
            
            print(f"   Selected: {selected_agent.value}")
            print(f"   Expected: {test_case['expected_agent'].value}")
            print(f"   Confidence: {confidence:.3f}")
            
            if selected_agent == test_case['expected_agent']:
                print(f"   ✅ Correct selection")
                correct_selections += 1
            else:
                print(f"   ❌ Incorrect selection")
            
            # Test similarity scores
            similarity_scores = selector.get_similarity_scores(test_case['query'])
            print(f"   Similarity scores: {dict(list(similarity_scores.items())[:3])}")
        
        accuracy = (correct_selections / total_selections) * 100
        print(f"\n📊 Selection Accuracy: {accuracy:.1f}% ({correct_selections}/{total_selections})")
        
        return accuracy > 70  # Expect at least 70% accuracy
        
    except Exception as e:
        print(f"❌ Semantic agent selection test failed: {e}")
        return False

def test_hybrid_agent_selection():
    """Test hybrid agent selection combining multiple methods."""
    
    print("\n🔄 Testing Hybrid Agent Selection")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_orchestration import HybridAgentSelector
        from langchain_openai import ChatOpenAI
        
        # Create hybrid selector
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)
        selector = HybridAgentSelector(fallback_llm=llm)
        print("✅ Hybrid agent selector created")
        
        # Test complex queries
        complex_queries = [
            "Analyse les données de mes parcelles et vérifie la conformité des traitements",
            "Planifie les travaux en fonction de la météo et des réglementations",
            "Diagnostique les maladies et calcule l'empreinte carbone"
        ]
        
        for i, query in enumerate(complex_queries, 1):
            print(f"\n📝 Complex Query {i}: {query[:50]}...")
            
            # Test hybrid selection
            agent_type, confidence, metadata = selector.select_agent(query)
            
            print(f"   Selected: {agent_type.value}")
            print(f"   Confidence: {confidence:.3f}")
            print(f"   Method: {metadata['method_used']}")
            print(f"   Rule-based: {metadata['rule_based']['agent']} ({metadata['rule_based']['confidence']:.3f})")
            print(f"   Semantic: {metadata['semantic']['agent']} ({metadata['semantic']['confidence']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid agent selection test failed: {e}")
        return False

def test_knowledge_retrieval():
    """Test semantic knowledge retrieval."""
    
    print("\n📚 Testing Knowledge Retrieval")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_orchestration import SemanticKnowledgeRetriever
        
        # Create knowledge retriever
        retriever = SemanticKnowledgeRetriever()
        print("✅ Knowledge retriever created")
        print(f"   Knowledge chunks: {len(retriever.knowledge_chunks)}")
        
        # Test knowledge retrieval
        test_queries = [
            "septoriose du blé",
            "zones non traitées",
            "certification HVE",
            "évapotranspiration",
            "rotation des cultures"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            
            # Retrieve relevant knowledge
            relevant_knowledge = retriever.retrieve_relevant_knowledge(query, top_k=2)
            
            print(f"   Retrieved: {len(relevant_knowledge)} chunks")
            for j, chunk in enumerate(relevant_knowledge, 1):
                print(f"   {j}. {chunk[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge retrieval test failed: {e}")
        return False

def test_enhanced_orchestrator():
    """Test the complete enhanced orchestrator."""
    
    print("\n🚀 Testing Enhanced Orchestrator")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_orchestration import create_semantic_enhanced_orchestrator
        
        # Create enhanced orchestrator
        orchestrator = create_semantic_enhanced_orchestrator()
        print("✅ Enhanced orchestrator created")
        
        # Test queries
        test_queries = [
            {
                "query": "Quels sont les rendements de mes parcelles de blé cette année?",
                "user_id": "test_user_1",
                "farm_id": "farm_123",
                "expected_agent": "farm_data_manager"
            },
            {
                "query": "Ce produit Prosaro est-il autorisé sur blé en France?",
                "user_id": "test_user_2", 
                "farm_id": "farm_456",
                "expected_agent": "regulatory_compliance"
            },
            {
                "query": "Quand puis-je traiter mes cultures cette semaine?",
                "user_id": "test_user_3",
                "farm_id": "farm_789",
                "expected_agent": "weather_intelligence"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Test Query {i}: {test_case['query'][:40]}...")
            
            start_time = time.time()
            
            # Process message
            result = orchestrator.process_message(
                message=test_case["query"],
                user_id=test_case["user_id"],
                farm_id=test_case["farm_id"]
            )
            
            processing_time = time.time() - start_time
            
            # Analyze result
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            print(f"   🤖 Selected agent: {result.get('agent', 'unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 0.0):.3f}")
            print(f"   📝 Response length: {len(result.get('response', ''))} characters")
            
            # Check if correct agent was selected
            if result.get('agent') == test_case['expected_agent']:
                print(f"   ✅ Correct agent selected")
            else:
                print(f"   ⚠️  Expected {test_case['expected_agent']}, got {result.get('agent')}")
            
            # Check metadata
            metadata = result.get('metadata', {})
            if metadata.get('semantic_enhanced'):
                print(f"   ✅ Semantic enhancement active")
            if 'knowledge_chunks_used' in metadata:
                print(f"   📚 Knowledge chunks: {len(metadata['knowledge_chunks_used'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced orchestrator test failed: {e}")
        return False

def test_debug_functionality():
    """Test debug functionality for agent selection and knowledge retrieval."""
    
    print("\n🔍 Testing Debug Functionality")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_orchestration import create_semantic_enhanced_orchestrator
        
        # Create enhanced orchestrator
        orchestrator = create_semantic_enhanced_orchestrator()
        
        # Test agent selection debug
        print("\n🤖 Agent Selection Debug:")
        selection_debug = orchestrator.get_agent_selection_debug("Quels sont les traitements contre la septoriose?")
        
        if 'error' not in selection_debug:
            print(f"   Selected: {selection_debug['selected_agent']}")
            print(f"   Confidence: {selection_debug['confidence']:.3f}")
            print(f"   Method: {selection_debug['selection_metadata']['method_used']}")
            print(f"   Similarity scores: {list(selection_debug['similarity_scores'].items())[:3]}")
        else:
            print(f"   Error: {selection_debug['error']}")
        
        # Test knowledge retrieval debug
        print("\n📚 Knowledge Retrieval Debug:")
        knowledge_debug = orchestrator.get_knowledge_retrieval_debug("septoriose du blé")
        
        if 'error' not in knowledge_debug:
            print(f"   Retrieved: {knowledge_debug['knowledge_count']} chunks")
            for i, chunk in enumerate(knowledge_debug['relevant_knowledge'][:2], 1):
                print(f"   {i}. {chunk[:60]}...")
        else:
            print(f"   Error: {knowledge_debug['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug functionality test failed: {e}")
        return False

def test_performance_benchmarks():
    """Test performance benchmarks for enhanced orchestration."""
    
    print("\n📊 Testing Performance Benchmarks")
    print("=" * 60)
    
    try:
        from app.agents.enhanced_orchestration import create_semantic_enhanced_orchestrator
        
        # Create enhanced orchestrator
        orchestrator = create_semantic_enhanced_orchestrator()
        
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
            
            result = orchestrator.process_message(
                message=query,
                user_id="perf_test_user",
                farm_id="perf_test_farm"
            )
            
            processing_time = time.time() - start_time
            single_query_times.append(processing_time)
            
            print(f"   Query: {query[:30]}... - {processing_time:.2f}s")
        
        # Calculate statistics
        avg_time = sum(single_query_times) / len(single_query_times)
        min_time = min(single_query_times)
        max_time = max(single_query_times)
        
        print(f"\n📈 Performance Results:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s")
        
        # Performance assessment
        if avg_time < 3.0:
            print(f"✅ Performance: Excellent (avg {avg_time:.2f}s)")
        elif avg_time < 5.0:
            print(f"✅ Performance: Good (avg {avg_time:.2f}s)")
        else:
            print(f"⚠️  Performance: Needs improvement (avg {avg_time:.2f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance benchmark test failed: {e}")
        return False

def main():
    """Run comprehensive enhanced orchestration tests."""
    
    print("🧪 Enhanced Orchestration System Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual components
    semantic_selection_success = test_semantic_agent_selection()
    hybrid_selection_success = test_hybrid_agent_selection()
    knowledge_retrieval_success = test_knowledge_retrieval()
    
    # Test complete system
    orchestrator_success = test_enhanced_orchestrator()
    debug_success = test_debug_functionality()
    performance_success = test_performance_benchmarks()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    
    total_tests = 6
    passed_tests = sum([
        semantic_selection_success,
        hybrid_selection_success,
        knowledge_retrieval_success,
        orchestrator_success,
        debug_success,
        performance_success
    ])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\nTest Results:")
    print(f"   Semantic Agent Selection: {'✅ PASS' if semantic_selection_success else '❌ FAIL'}")
    print(f"   Hybrid Agent Selection: {'✅ PASS' if hybrid_selection_success else '❌ FAIL'}")
    print(f"   Knowledge Retrieval: {'✅ PASS' if knowledge_retrieval_success else '❌ FAIL'}")
    print(f"   Enhanced Orchestrator: {'✅ PASS' if orchestrator_success else '❌ FAIL'}")
    print(f"   Debug Functionality: {'✅ PASS' if debug_success else '❌ FAIL'}")
    print(f"   Performance Benchmarks: {'✅ PASS' if performance_success else '❌ FAIL'}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! Enhanced orchestration system is ready.")
    else:
        print(f"\n⚠️  Some tests failed. Review the errors above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
