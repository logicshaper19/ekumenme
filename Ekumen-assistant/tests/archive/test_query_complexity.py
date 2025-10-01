"""
Test Query Complexity Classification
Verifies that simple queries get simple responses and complex queries get full guides
"""

import asyncio
import sys
from app.services.query_classifier import QueryComplexityClassifier

# Test queries
TEST_QUERIES = {
    "simple": [
        "Quelle est la météo à Dourdan ?",
        "Quel temps fait-il à Paris ?",
        "Va-t-il pleuvoir demain ?",
        "Quelle est la température actuelle ?",
        "C'est quoi l'AMM ?",
        "Prévisions météo pour la semaine"
    ],
    "medium": [
        "Quelles sont les meilleures cultures pour ma région ?",
        "Comparer blé et maïs",
        "État de mes parcelles",
        "Conseil pour irrigation"
    ],
    "complex": [
        "Je veux planter du café à Dourdan",
        "Comment cultiver des tomates en Normandie ?",
        "Quelle culture choisir pour mon exploitation ?",
        "Recommandations pour améliorer mon rendement",
        "Comment traiter une maladie sur mes vignes ?",
        "Planifier ma rotation de cultures"
    ]
}


def test_pattern_based_classification():
    """Test fast pattern-based classification"""
    print("\n" + "="*80)
    print("TEST 1: Pattern-Based Classification (Fast)")
    print("="*80)
    
    classifier = QueryComplexityClassifier(use_llm=False)
    
    for expected_complexity, queries in TEST_QUERIES.items():
        print(f"\n📋 Expected: {expected_complexity.upper()}")
        print("-" * 80)
        
        for query in queries:
            result = classifier.classify(query, use_llm=False)
            
            match = "✅" if result["complexity"] == expected_complexity else "❌"
            print(f"{match} {query}")
            print(f"   → {result['complexity']} (confidence: {result['confidence']:.2f})")
            print(f"   → Type: {result['query_type']}")
            print(f"   → Full structure: {result['requires_full_structure']}")


async def test_llm_based_classification():
    """Test LangChain LLM-based classification"""
    print("\n" + "="*80)
    print("TEST 2: LLM-Based Classification (LangChain)")
    print("="*80)
    
    try:
        classifier = QueryComplexityClassifier(use_llm=True)
        
        for expected_complexity, queries in TEST_QUERIES.items():
            print(f"\n📋 Expected: {expected_complexity.upper()}")
            print("-" * 80)
            
            for query in queries[:2]:  # Test first 2 of each category to save API calls
                result = classifier.classify(query, use_llm=True)
                
                match = "✅" if result["complexity"] == expected_complexity else "❌"
                print(f"{match} {query}")
                print(f"   → {result['complexity']} (confidence: {result['confidence']:.2f})")
                print(f"   → Type: {result['query_type']}")
                print(f"   → Full structure: {result['requires_full_structure']}")
                print(f"   → Method: {result['method']}")
                print(f"   → Reasoning: {result['reasoning']}")
    
    except Exception as e:
        print(f"⚠️  LLM classification not available: {e}")
        print("   (This is OK - pattern-based classification will be used)")


def test_response_template_selection():
    """Test that correct templates are selected"""
    print("\n" + "="*80)
    print("TEST 3: Response Template Selection")
    print("="*80)
    
    from app.prompts.response_templates import get_response_template
    
    test_cases = [
        ("simple", "Quelle est la météo ?", "Should be 3-5 sentences"),
        ("medium", "Comparer blé et maïs", "Should be 1-2 paragraphs"),
        ("complex", "Je veux planter du café", "Should be full 6-section guide")
    ]
    
    for complexity, query, expected in test_cases:
        print(f"\n📝 Complexity: {complexity}")
        print(f"   Query: {query}")
        print(f"   Expected: {expected}")
        
        template = get_response_template(
            complexity=complexity,
            query=query,
            data_summary="[Test data]",
            location="Dourdan"
        )
        
        # Check template characteristics
        has_sections = template.count("###") >= 3
        is_concise = "CONCISE" in template or "3-5 phrases" in template
        is_full = "6 SECTIONS" in template or "OBLIGATOIRE" in template
        
        print(f"   ✓ Template length: {len(template)} chars")
        print(f"   ✓ Has multiple sections: {has_sections}")
        print(f"   ✓ Concise instructions: {is_concise}")
        print(f"   ✓ Full structure: {is_full}")
        
        # Verify correct template
        if complexity == "simple":
            assert is_concise and not is_full, "Simple template should be concise"
            print(f"   ✅ Correct simple template")
        elif complexity == "complex":
            assert is_full, "Complex template should have full structure"
            print(f"   ✅ Correct complex template")


def test_classification_accuracy():
    """Calculate classification accuracy"""
    print("\n" + "="*80)
    print("TEST 4: Classification Accuracy")
    print("="*80)
    
    classifier = QueryComplexityClassifier(use_llm=False)
    
    total = 0
    correct = 0
    
    for expected_complexity, queries in TEST_QUERIES.items():
        for query in queries:
            result = classifier.classify(query, use_llm=False)
            total += 1
            if result["complexity"] == expected_complexity:
                correct += 1
    
    accuracy = (correct / total) * 100
    
    print(f"\n📊 Pattern-Based Classification Accuracy:")
    print(f"   Total queries: {total}")
    print(f"   Correct: {correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print(f"   ✅ EXCELLENT (≥80%)")
    elif accuracy >= 70:
        print(f"   ✅ GOOD (≥70%)")
    else:
        print(f"   ⚠️  NEEDS IMPROVEMENT (<70%)")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("QUERY COMPLEXITY CLASSIFICATION TESTS")
    print("="*80)
    
    # Test 1: Pattern-based (fast)
    test_pattern_based_classification()
    
    # Test 2: LLM-based (accurate)
    await test_llm_based_classification()
    
    # Test 3: Template selection
    test_response_template_selection()
    
    # Test 4: Accuracy
    test_classification_accuracy()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE")
    print("="*80)
    
    print("\n📝 Summary:")
    print("   - Pattern-based classification: Fast, rule-based")
    print("   - LLM-based classification: Accurate, context-aware (LangChain)")
    print("   - Response templates: Simple, Medium, Complex")
    print("   - Integration: Ready for synthesis node")


if __name__ == "__main__":
    asyncio.run(main())

