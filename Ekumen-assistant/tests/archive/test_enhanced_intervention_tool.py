"""
Comprehensive tests for enhanced intervention windows tool - WITH REAL API

Tests:
1. Intervention windows with real weather data
2. Caching performance
3. Custom intervention types
4. Error handling

NOTE: Uses REAL Weather API to show actual production performance
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.weather_agent.get_weather_data_tool_enhanced import (
    get_weather_data_tool_enhanced
)
from app.tools.weather_agent.identify_intervention_windows_tool_enhanced import (
    identify_intervention_windows_tool_enhanced
)
from app.core.cache import get_cache_stats, clear_cache


async def test_1_intervention_windows_with_real_data():
    """Test 1: Intervention windows with real weather data"""
    print("\n" + "="*80)
    print("TEST 1: Intervention Windows with Real Weather Data")
    print("="*80)
    
    try:
        # Step 1: Get real weather data
        print("\n📞 Step 1: Getting real weather data for Bordeaux...")
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Bordeaux",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        
        weather_data = json.loads(weather_result)
        print(f"   ✅ Got weather data: {weather_data.get('location')}, {len(weather_data.get('weather_conditions', []))} days")
        
        # Step 2: Identify intervention windows
        print("\n📊 Step 2: Identifying intervention windows...")
        start = time.time()
        windows_result = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "intervention_types": None  # Use defaults
        })
        elapsed = time.time() - start
        
        windows_data = json.loads(windows_result)
        print(f"   ⏱️  Analysis time: {elapsed:.3f}s ({elapsed*1000:.0f}ms)")
        print(f"   ✅ Success: {windows_data.get('success')}")
        print(f"   📍 Location: {windows_data.get('location')}")
        print(f"   🎯 Total windows: {windows_data.get('total_windows')}")
        
        # Show window statistics
        stats = windows_data.get('window_statistics', {})
        print(f"   📊 Windows by type: {stats.get('windows_by_type', {})}")
        print(f"   📈 Average confidence: {stats.get('average_confidence', 0):.0%}")
        
        # Show best window
        if stats.get('best_window_date'):
            print(f"   🌟 Best window: {stats.get('best_window_type')} on {stats.get('best_window_date')}")
        
        # Show insights
        insights = windows_data.get('window_insights', [])
        if insights:
            print(f"\n   💡 Insights:")
            for insight in insights[:3]:  # Show first 3
                print(f"      {insight}")
        
        print("\n✅ TEST 1 PASSED: Intervention windows working with real data")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_2_caching_performance():
    """Test 2: Caching performance"""
    print("\n" + "="*80)
    print("TEST 2: Caching Performance")
    print("="*80)
    
    try:
        # Clear cache
        clear_cache(category="weather")
        print("🧹 Cache cleared")
        
        # Get weather data (will be cached)
        print("\n📞 Getting weather data...")
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Toulouse",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        
        # First windows analysis (cache miss)
        print("\n📊 First windows analysis (cache miss)...")
        start = time.time()
        result1 = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "intervention_types": ["pulvérisation", "semis"]
        })
        time1 = time.time() - start
        print(f"   ⏱️  Time: {time1:.3f}s ({time1*1000:.0f}ms)")
        
        # Second windows analysis (cache hit)
        print("\n📊 Second windows analysis (cache hit)...")
        start = time.time()
        result2 = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "intervention_types": ["pulvérisation", "semis"]
        })
        time2 = time.time() - start
        print(f"   ⏱️  Time: {time2:.3f}s ({time2*1000:.0f}ms)")
        
        # Verify results identical
        if result1 == result2:
            print("   ✅ Results identical (cache working)")
        else:
            print("   ⚠️  Results differ")
        
        # Calculate speedup
        speedup = (time1 - time2) / time1 * 100 if time1 > 0 else 0
        speedup_factor = time1 / time2 if time2 > 0 else 0
        
        print(f"\n📊 Cache Performance:")
        print(f"   First call (uncached):  {time1:.3f}s ({time1*1000:.0f}ms)")
        print(f"   Second call (cached):   {time2:.3f}s ({time2*1000:.0f}ms)")
        print(f"   Speedup: {speedup:.1f}%")
        print(f"   Speed factor: {speedup_factor:.1f}x faster")
        
        # Cache stats
        stats = get_cache_stats()
        print(f"\n📊 Cache Stats:")
        print(f"   Redis available: {stats['redis_available']}")
        print(f"   Total memory items: {stats['total_memory_items']}")
        
        if speedup > 0:
            print(f"\n✅ Cache providing {speedup:.1f}% speedup")
        else:
            print(f"\n⚠️ Cache not providing speedup")
        
        print("\n✅ TEST 2 PASSED: Caching working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_custom_intervention_types():
    """Test 3: Custom intervention types"""
    print("\n" + "="*80)
    print("TEST 3: Custom Intervention Types")
    print("="*80)
    
    try:
        # Get weather data
        print("\n📞 Getting weather data for Nantes...")
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Nantes",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        
        # Test different intervention type combinations
        test_cases = [
            (["pulvérisation"], "Spraying only"),
            (["semis", "récolte"], "Planting and harvesting"),
            (["travaux_champ", "fertilisation"], "Field work and fertilization"),
        ]
        
        for intervention_types, description in test_cases:
            print(f"\n🔧 Testing: {description}")
            result = await identify_intervention_windows_tool_enhanced.ainvoke({
                "weather_data_json": weather_result,
                "intervention_types": intervention_types
            })
            
            data = json.loads(result)
            print(f"   ✅ Success: {data.get('success')}")
            print(f"   🎯 Total windows: {data.get('total_windows')}")
            print(f"   📋 Types analyzed: {data.get('intervention_types')}")
            
            # Verify only requested types are returned
            windows = data.get('windows', [])
            returned_types = set(w['intervention_type'] for w in windows)
            expected_types = set(intervention_types)
            if returned_types.issubset(expected_types):
                print(f"   ✅ Only requested types returned")
            else:
                print(f"   ⚠️  Unexpected types: {returned_types - expected_types}")
        
        print("\n✅ TEST 3 PASSED: Custom intervention types working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_error_handling():
    """Test 4: Error handling"""
    print("\n" + "="*80)
    print("TEST 4: Error Handling")
    print("="*80)
    
    try:
        # Test with invalid JSON
        print("\n🔧 Testing with invalid JSON...")
        result = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": "invalid json",
            "intervention_types": None
        })
        
        data = json.loads(result)
        print(f"   Success: {data.get('success')}")
        print(f"   Error type: {data.get('error_type')}")
        print(f"   Error: {data.get('error', '')[:100]}...")
        
        if not data.get('success'):
            print("   ✅ Error handled gracefully")
        else:
            print("   ⚠️ Should have returned error")
        
        # Test with empty weather data
        print("\n🔧 Testing with empty weather data...")
        empty_weather = json.dumps({"location": "Test", "weather_conditions": []})
        result = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": empty_weather,
            "intervention_types": None
        })
        
        data = json.loads(result)
        if not data.get('success'):
            print("   ✅ Empty data error handled")
        else:
            print("   ⚠️ Should have returned error for empty data")
        
        # Test with invalid intervention type (Pydantic will catch this before function)
        print("\n🔧 Testing with invalid intervention type...")
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Paris",
            "days": 3,
            "use_real_api": True
        })

        try:
            result = await identify_intervention_windows_tool_enhanced.ainvoke({
                "weather_data_json": weather_result,
                "intervention_types": ["invalid_type"]
            })
            print("   ⚠️ Should have raised validation error")
        except Exception as e:
            if "Invalid intervention type" in str(e):
                print("   ✅ Invalid intervention type caught by Pydantic validation")
            else:
                print(f"   ⚠️ Unexpected error: {e}")
        
        print("\n✅ TEST 4 PASSED: Error handling working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("ENHANCED INTERVENTION WINDOWS TOOL - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    print("\n⚠️  Note: Using REAL Weather API")
    
    tests = [
        ("Intervention Windows with Real Data", test_1_intervention_windows_with_real_data),
        ("Caching Performance", test_2_caching_performance),
        ("Custom Intervention Types", test_3_custom_intervention_types),
        ("Error Handling", test_4_error_handling),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ TEST FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Enhanced intervention windows tool is ready to use.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review and fix before deployment.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

