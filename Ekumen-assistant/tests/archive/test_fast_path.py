"""
Test Fast Path Query Service
Verify that simple queries are processed quickly (< 5 seconds)
"""

import asyncio
import time
from app.services.fast_query_service import FastQueryService
from app.services.streaming_service import StreamingService


async def test_fast_query_service():
    """Test fast query service directly"""
    print("=" * 60)
    print("TEST 1: Fast Query Service (Direct)")
    print("=" * 60)
    
    service = FastQueryService()
    
    # Test queries
    test_queries = [
        "Quelle est la météo à Dourdan ?",
        "Quel temps fait-il aujourd'hui ?",
        "Est-ce qu'il va pleuvoir ?",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        # Check if fast path should be used
        should_use_fast = service.should_use_fast_path(query)
        print(f"   Fast path: {'✅ YES' if should_use_fast else '❌ NO'}")
        
        if should_use_fast:
            # Time the query
            start = time.time()
            result = await service.process_fast_query(query)
            duration = time.time() - start
            
            print(f"   Duration: {duration:.2f}s")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Agent: {result['agent_type']}")
            
            # Check if it's fast enough
            if duration < 5.0:
                print(f"   ✅ FAST (< 5s)")
            else:
                print(f"   ⚠️  SLOW (> 5s)")


async def test_streaming_service_routing():
    """Test streaming service routing to fast path"""
    print("\n" + "=" * 60)
    print("TEST 2: Streaming Service Routing")
    print("=" * 60)
    
    service = StreamingService()
    
    # Test queries
    test_queries = [
        ("Quelle est la météo à Dourdan ?", True),  # Should use fast path
        ("Analyse la faisabilité de cultiver du café à Dourdan", False),  # Should use workflow
    ]
    
    for query, expected_fast in test_queries:
        print(f"\n📝 Query: {query}")
        print(f"   Expected: {'FAST PATH' if expected_fast else 'WORKFLOW'}")
        
        # Check routing decision
        if service.fast_service:
            should_use_fast = service.fast_service.should_use_fast_path(query)
            print(f"   Actual: {'FAST PATH' if should_use_fast else 'WORKFLOW'}")
            
            if should_use_fast == expected_fast:
                print(f"   ✅ CORRECT ROUTING")
            else:
                print(f"   ❌ WRONG ROUTING")
        
        # Time the full streaming response
        start = time.time()
        chunks = []
        
        async for chunk in service.stream_response(query, use_workflow=True):
            chunks.append(chunk)
            if chunk.get("type") == "workflow_result":
                break
        
        duration = time.time() - start
        print(f"   Duration: {duration:.2f}s")
        
        # Check performance
        if expected_fast and duration < 5.0:
            print(f"   ✅ FAST ENOUGH")
        elif not expected_fast and duration < 60.0:
            print(f"   ✅ REASONABLE")
        else:
            print(f"   ⚠️  TOO SLOW")


async def test_fast_path_classification():
    """Test query classification for fast path"""
    print("\n" + "=" * 60)
    print("TEST 3: Fast Path Classification")
    print("=" * 60)
    
    service = FastQueryService()
    
    # Test cases: (query, should_be_fast)
    test_cases = [
        # Should use fast path
        ("Quelle est la météo à Dourdan ?", True),
        ("Quel temps fait-il ?", True),
        ("Est-ce qu'il va pleuvoir ?", True),
        ("Quelle température aujourd'hui ?", True),
        
        # Should NOT use fast path (complex)
        ("Analyse la faisabilité de cultiver du café", False),
        ("Compare les tendances météo des 5 dernières années", False),
        ("Quelle est la meilleure stratégie de traitement ?", False),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for query, expected_fast in test_cases:
        actual_fast = service.should_use_fast_path(query)
        
        status = "✅" if actual_fast == expected_fast else "❌"
        print(f"{status} {query[:50]:<50} | Expected: {expected_fast:5} | Actual: {actual_fast:5}")
        
        if actual_fast == expected_fast:
            correct += 1
    
    print(f"\n📊 Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")


async def main():
    """Run all tests"""
    print("\n🚀 FAST PATH OPTIMIZATION TESTS\n")
    
    try:
        # Test 1: Direct fast query service
        await test_fast_query_service()
        
        # Test 2: Streaming service routing
        await test_streaming_service_routing()
        
        # Test 3: Classification accuracy
        await test_fast_path_classification()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

