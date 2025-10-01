#!/usr/bin/env python3
"""
Comprehensive test suite for Semantic Tool Selector
Tests production-ready features including configuration-based profiles, consistent scoring, and robust fallback mechanisms.
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.semantic_tool_selector import (
    SemanticToolSelector,
    ToolSelectionResult,
    LanguageDetector,
    ScoringNormalizer,
    semantic_tool_selector
)

def test_language_detection():
    """Test language detection functionality."""
    print("🔍 Testing Language Detection...")
    
    detector = LanguageDetector()
    
    test_cases = [
        ("Mon blé présente des taches brunes", "fr"),
        ("My wheat shows brown spots", "en"),
        ("Diagnostic de maladie sur colza", "fr"),
        ("Disease diagnosis on rapeseed", "en"),
        ("Planification des travaux agricoles", "fr"),
        ("Agricultural work planning", "en"),
        ("Vérifier la conformité réglementaire", "fr"),
        ("Check regulatory compliance", "en")
    ]
    
    correct = 0
    for text, expected_lang in test_cases:
        detected = detector.detect_language(text)
        if detected == expected_lang:
            correct += 1
            print(f"  ✅ '{text[:30]}...' → {detected}")
        else:
            print(f"  ❌ '{text[:30]}...' → {detected} (expected {expected_lang})")
    
    accuracy = correct / len(test_cases)
    print(f"  📊 Language Detection Accuracy: {accuracy:.1%} ({correct}/{len(test_cases)})")
    return accuracy > 0.8

def test_scoring_normalization():
    """Test scoring normalization consistency."""
    print("\n📊 Testing Scoring Normalization...")
    
    normalizer = ScoringNormalizer()
    
    # Test semantic score normalization
    semantic_scores = [0.0, 0.5, 0.8, 1.0, 1.2, -0.1]
    print("  Semantic Score Normalization:")
    for score in semantic_scores:
        normalized = normalizer.normalize_semantic_score(score)
        print(f"    {score} → {normalized:.3f}")
        assert 0.0 <= normalized <= 1.0, f"Score {normalized} out of range"
    
    # Test keyword score normalization
    print("  Keyword Score Normalization:")
    test_cases = [
        (0, 5, 10),  # no matches
        (2, 5, 20),  # some matches
        (5, 5, 30),  # all matches
        (3, 10, 50)  # partial matches, long query
    ]
    
    for matches, total_keywords, query_length in test_cases:
        normalized = normalizer.normalize_keyword_score(matches, total_keywords, query_length)
        print(f"    {matches}/{total_keywords} keywords, query_len={query_length} → {normalized:.3f}")
        assert 0.0 <= normalized <= 1.0, f"Score {normalized} out of range"
    
    # Test intent score normalization
    print("  Intent Score Normalization:")
    intent_cases = [
        (0, 3, 1.0),  # no patterns
        (1, 3, 1.0),  # some patterns
        (3, 3, 1.1),  # all patterns with boost
        (2, 5, 0.9)   # partial with penalty
    ]
    
    for pattern_matches, total_patterns, confidence_modifier in intent_cases:
        normalized = normalizer.normalize_intent_score(pattern_matches, total_patterns, confidence_modifier)
        print(f"    {pattern_matches}/{total_patterns} patterns, modifier={confidence_modifier} → {normalized:.3f}")
        assert 0.0 <= normalized <= 1.0, f"Score {normalized} out of range"
    
    print("  ✅ All scoring normalization tests passed")
    return True

def test_configuration_loading():
    """Test configuration-based tool profile loading."""
    print("\n📁 Testing Configuration Loading...")
    
    try:
        selector = SemanticToolSelector()
        
        # Check configuration loaded
        assert selector.config is not None, "Configuration not loaded"
        assert 'tools' in selector.config, "Tools section missing from configuration"
        assert 'scoring_config' in selector.config, "Scoring config missing"
        
        # Check tool profiles loaded
        assert len(selector.tool_profiles) > 0, "No tool profiles loaded"
        
        print(f"  ✅ Loaded {len(selector.tool_profiles)} tool profiles")
        print(f"  ✅ Configuration version: {selector.config.get('version', 'unknown')}")
        
        # Check specific tools
        expected_tools = [
            'diagnose_disease_tool',
            'identify_pest_tool',
            'generate_planning_tasks_tool',
            'check_regulatory_compliance_tool'
        ]
        
        for tool_id in expected_tools:
            if tool_id in selector.tool_profiles:
                profile = selector.tool_profiles[tool_id]
                print(f"    ✅ {tool_id}: {profile.domain}/{profile.subdomain}")
            else:
                print(f"    ❌ Missing tool: {tool_id}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration loading failed: {e}")
        return False

def test_tool_selection_methods():
    """Test different tool selection methods."""
    print("\n🎯 Testing Tool Selection Methods...")
    
    selector = SemanticToolSelector()
    
    # Test queries in French
    test_queries = [
        {
            "query": "Mon blé présente des taches brunes circulaires avec jaunissement",
            "expected_domain": "crop_health",
            "description": "Disease symptoms"
        },
        {
            "query": "Identifier les ravageurs qui font des trous dans les feuilles de colza",
            "expected_domain": "crop_health", 
            "description": "Pest identification"
        },
        {
            "query": "Planifier les travaux de semis pour optimiser le rendement",
            "expected_domain": "planning",
            "description": "Planning optimization"
        },
        {
            "query": "Vérifier la conformité du traitement phytosanitaire",
            "expected_domain": "regulatory",
            "description": "Regulatory compliance"
        },
        {
            "query": "Recherche AMM pour herbicide sur blé",
            "expected_domain": "regulatory",
            "description": "AMM lookup"
        },
        {
            "query": "Prévisions météo pour la semaine prochaine",
            "expected_domain": "weather",
            "description": "Weather forecast"
        }
    ]
    
    available_tools = list(selector.tool_profiles.keys())
    methods = ["keyword", "intent", "hybrid"]
    
    results = {}
    
    for method in methods:
        print(f"\n  Testing {method.upper()} method:")
        method_results = []
        
        for test_case in test_queries:
            query = test_case["query"]
            expected_domain = test_case["expected_domain"]
            
            result = selector.select_tools(
                message=query,
                available_tools=available_tools,
                method=method,
                threshold=0.3,
                max_tools=2
            )
            
            # Check if selected tools match expected domain
            domain_match = False
            if result.selected_tools:
                for tool_id in result.selected_tools:
                    if selector.tool_profiles[tool_id].domain == expected_domain:
                        domain_match = True
                        break
            
            method_results.append({
                'query': test_case["description"],
                'domain_match': domain_match,
                'confidence': result.overall_confidence,
                'selected_tools': result.selected_tools,
                'confidence_tier': result.confidence_tier
            })
            
            status = "✅" if domain_match else "❌"
            print(f"    {status} {test_case['description']}: {result.selected_tools} (conf: {result.overall_confidence:.3f})")
        
        # Calculate method accuracy
        accuracy = sum(1 for r in method_results if r['domain_match']) / len(method_results)
        avg_confidence = sum(r['confidence'] for r in method_results) / len(method_results)
        
        results[method] = {
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'results': method_results
        }
        
        print(f"    📊 {method.upper()} Accuracy: {accuracy:.1%}, Avg Confidence: {avg_confidence:.3f}")
    
    return results

def test_fallback_mechanisms():
    """Test fallback mechanisms for edge cases."""
    print("\n🔄 Testing Fallback Mechanisms...")
    
    selector = SemanticToolSelector()
    available_tools = list(selector.tool_profiles.keys())
    
    # Test with very high threshold (should trigger fallback)
    result = selector.select_tools(
        message="Mon blé a des problèmes",
        available_tools=available_tools,
        method="hybrid",
        threshold=0.95,  # Very high threshold
        max_tools=2
    )
    
    print(f"  High threshold test:")
    print(f"    Fallback applied: {result.fallback_applied}")
    print(f"    Selected tools: {result.selected_tools}")
    print(f"    Reasoning: {result.reasoning}")
    
    # Test with nonsensical query
    result = selector.select_tools(
        message="xyz abc def random words",
        available_tools=available_tools,
        method="hybrid",
        threshold=0.4,
        max_tools=2
    )
    
    print(f"  Nonsensical query test:")
    print(f"    Fallback applied: {result.fallback_applied}")
    print(f"    Selected tools: {result.selected_tools}")
    print(f"    Confidence: {result.overall_confidence:.3f}")
    
    # Test with empty available tools
    result = selector.select_tools(
        message="Mon blé a des problèmes",
        available_tools=[],
        method="hybrid",
        threshold=0.4,
        max_tools=2
    )
    
    print(f"  Empty tools test:")
    print(f"    Selected tools: {result.selected_tools}")
    print(f"    Reasoning: {result.reasoning}")
    
    return True

def test_performance():
    """Test performance characteristics."""
    print("\n⚡ Testing Performance...")
    
    selector = SemanticToolSelector()
    available_tools = list(selector.tool_profiles.keys())
    
    # Test queries
    queries = [
        "Mon blé présente des taches brunes",
        "Identifier les ravageurs sur colza",
        "Planifier les travaux agricoles",
        "Vérifier la conformité réglementaire",
        "Prévisions météo pour demain"
    ]
    
    # Warm up
    for query in queries[:2]:
        selector.select_tools(query, available_tools, "hybrid", 0.4, 2)
    
    # Performance test
    start_time = time.time()
    iterations = 100
    
    for i in range(iterations):
        query = queries[i % len(queries)]
        result = selector.select_tools(query, available_tools, "hybrid", 0.4, 2)
    
    end_time = time.time()
    total_time = (end_time - start_time) * 1000  # Convert to milliseconds
    avg_time = total_time / iterations
    queries_per_second = 1000 / avg_time
    
    print(f"  📊 Performance Results:")
    print(f"    Total time: {total_time:.1f}ms")
    print(f"    Average time per query: {avg_time:.2f}ms")
    print(f"    Queries per second: {queries_per_second:.0f}")
    
    # Get performance stats
    stats = selector.get_performance_stats()
    print(f"    Total queries processed: {stats['total_queries']}")
    print(f"    Average response time: {stats['avg_response_time_ms']:.2f}ms")
    
    return queries_per_second > 100  # Should handle at least 100 queries per second

def run_all_tests():
    """Run comprehensive test suite."""
    print("🧪 Semantic Tool Selector - Comprehensive Test Suite")
    print("=" * 70)
    
    tests = [
        ("Language Detection", test_language_detection),
        ("Scoring Normalization", test_scoring_normalization),
        ("Configuration Loading", test_configuration_loading),
        ("Tool Selection Methods", test_tool_selection_methods),
        ("Fallback Mechanisms", test_fallback_mechanisms),
        ("Performance", test_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"\n❌ ERROR in {test_name}: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All tests passed! Semantic Tool Selector is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
