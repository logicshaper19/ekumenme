"""
Test Response Formatting
Verify that responses follow the correct formatting rules:
- No ## or ### headings
- No emojis
- Bold headings instead
- Bullet points for lists
"""

import asyncio
import re
from app.services.fast_query_service import FastQueryService
from app.services.streaming_service import StreamingService


def check_formatting(response: str) -> dict:
    """
    Check if response follows formatting rules
    
    Returns dict with:
    - has_markdown_headings: bool
    - has_emojis: bool
    - has_bold_headings: bool
    - has_bullet_points: bool
    """
    # Check for markdown headings (##, ###)
    has_markdown_headings = bool(re.search(r'^#{2,3}\s', response, re.MULTILINE))
    
    # Check for emojis (common ones used in agricultural context)
    emoji_pattern = r'[🌱🌾⚠️✅❌🌡️💧⏱️💰🌳🏠❄️💪🌤️☁️🌧️🌦️☀️]'
    has_emojis = bool(re.search(emoji_pattern, response))
    
    # Check for bold headings (pattern: **Text:**)
    has_bold_headings = bool(re.search(r'\*\*[^*]+:\*\*', response))
    
    # Check for bullet points
    has_bullet_points = bool(re.search(r'^\s*[-•]\s', response, re.MULTILINE))
    
    return {
        'has_markdown_headings': has_markdown_headings,
        'has_emojis': has_emojis,
        'has_bold_headings': has_bold_headings,
        'has_bullet_points': has_bullet_points
    }


def print_formatting_report(response: str, query: str):
    """Print formatting analysis"""
    print(f"\n{'='*60}")
    print(f"Query: {query[:50]}...")
    print(f"{'='*60}")
    
    checks = check_formatting(response)
    
    # Check for violations
    violations = []
    if checks['has_markdown_headings']:
        violations.append("❌ Uses ## or ### headings (should use **Bold:**)")
    if checks['has_emojis']:
        violations.append("❌ Contains emojis (should not use emojis)")
    
    # Check for correct formatting
    correct = []
    if checks['has_bold_headings']:
        correct.append("✅ Uses **Bold:** headings")
    if checks['has_bullet_points']:
        correct.append("✅ Uses bullet points")
    
    # Print results
    if violations:
        print("\n🚨 FORMATTING VIOLATIONS:")
        for v in violations:
            print(f"  {v}")
    else:
        print("\n✅ NO VIOLATIONS")
    
    if correct:
        print("\n✅ CORRECT FORMATTING:")
        for c in correct:
            print(f"  {c}")
    
    # Print response preview
    print(f"\n📝 RESPONSE PREVIEW:")
    print(f"{response[:200]}...")
    
    # Overall score
    score = (2 - len(violations)) / 2 * 100
    print(f"\n📊 FORMATTING SCORE: {score:.0f}%")
    
    return len(violations) == 0


async def test_fast_query_formatting():
    """Test fast query service formatting"""
    print("\n" + "="*60)
    print("TEST 1: Fast Query Service Formatting")
    print("="*60)
    
    service = FastQueryService()
    
    test_queries = [
        "Quelle est la météo à Dourdan ?",
        "Quel temps fait-il aujourd'hui ?",
    ]
    
    all_passed = True
    
    for query in test_queries:
        result = await service.process_fast_query(query)
        response = result['response']
        
        passed = print_formatting_report(response, query)
        if not passed:
            all_passed = False
    
    return all_passed


async def test_streaming_service_formatting():
    """Test streaming service formatting"""
    print("\n" + "="*60)
    print("TEST 2: Streaming Service Formatting")
    print("="*60)
    
    service = StreamingService()
    
    test_queries = [
        "Quelle est la météo à Dourdan ?",
        "Comment protéger mes plants de colza contre les limaces ?",
    ]
    
    all_passed = True
    
    for query in test_queries:
        # Collect full response
        response = ""
        async for chunk in service.stream_response(query, use_workflow=True):
            if chunk.get("type") == "workflow_result":
                response = chunk.get("response", "")
                break
        
        if response:
            passed = print_formatting_report(response, query)
            if not passed:
                all_passed = False
        else:
            print(f"\n⚠️  No response received for: {query}")
            all_passed = False
    
    return all_passed


async def test_specific_violations():
    """Test for specific formatting violations"""
    print("\n" + "="*60)
    print("TEST 3: Specific Violation Detection")
    print("="*60)
    
    # Test cases with known violations
    test_cases = [
        {
            "response": "## 🌱 Titre\nContenu",
            "expected_violations": ["markdown_headings", "emojis"],
            "description": "Markdown heading with emoji"
        },
        {
            "response": "### Sous-titre\nContenu",
            "expected_violations": ["markdown_headings"],
            "description": "Markdown sub-heading"
        },
        {
            "response": "**Titre Correct:**\nContenu avec 🌱 emoji",
            "expected_violations": ["emojis"],
            "description": "Bold heading but with emoji"
        },
        {
            "response": "**Titre Correct:**\n- Point 1\n- Point 2",
            "expected_violations": [],
            "description": "Correct formatting"
        },
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test['description']} ---")
        
        checks = check_formatting(test['response'])
        
        # Check for expected violations
        found_violations = []
        if checks['has_markdown_headings']:
            found_violations.append("markdown_headings")
        if checks['has_emojis']:
            found_violations.append("emojis")
        
        expected = set(test['expected_violations'])
        found = set(found_violations)
        
        if expected == found:
            print(f"✅ PASS: Found expected violations: {found or 'none'}")
        else:
            print(f"❌ FAIL: Expected {expected}, found {found}")
            all_passed = False
    
    return all_passed


async def main():
    """Run all formatting tests"""
    print("\n🧪 RESPONSE FORMATTING TESTS\n")
    
    try:
        # Test 1: Fast query formatting
        test1_passed = await test_fast_query_formatting()
        
        # Test 2: Streaming service formatting
        test2_passed = await test_streaming_service_formatting()
        
        # Test 3: Specific violation detection
        test3_passed = await test_specific_violations()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Test 1 (Fast Query): {'✅ PASS' if test1_passed else '❌ FAIL'}")
        print(f"Test 2 (Streaming): {'✅ PASS' if test2_passed else '❌ FAIL'}")
        print(f"Test 3 (Violations): {'✅ PASS' if test3_passed else '❌ FAIL'}")
        
        if test1_passed and test2_passed and test3_passed:
            print("\n✅ ALL TESTS PASSED")
        else:
            print("\n❌ SOME TESTS FAILED")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

