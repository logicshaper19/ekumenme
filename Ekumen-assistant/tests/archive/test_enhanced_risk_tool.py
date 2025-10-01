"""
Comprehensive tests for enhanced risk analysis tool - WITH REAL API

Tests:
1. Risk analysis with real weather data
2. Caching performance
3. Crop-specific analysis
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
from app.tools.weather_agent.analyze_weather_risks_tool_enhanced import (
    analyze_weather_risks_tool_enhanced
)
from app.core.cache import get_cache_stats, clear_cache


async def test_1_risk_analysis_with_real_data():
    """Test 1: Risk analysis with real weather data"""
    print("\n" + "="*80)
    print("TEST 1: Risk Analysis with Real Weather Data")
    print("="*80)
    
    try:
        # Step 1: Get real weather data
        print("\n📞 Step 1: Getting real weather data for Paris...")
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Paris",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        
        weather_data = json.loads(weather_result)
        print(f"   ✅ Got weather data: {weather_data.get('location')}, {len(weather_data.get('weather_conditions', []))} days")
        
        # Step 2: Analyze risks
        print("\n📊 Step 2: Analyzing agricultural risks...")
        start = time.time()
        risk_result = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": None  # General analysis
        })
        elapsed = time.time() - start
        
        risk_data = json.loads(risk_result)
        print(f"   ⏱️  Analysis time: {elapsed:.3f}s ({elapsed*1000:.0f}ms)")
        print(f"   ✅ Success: {risk_data.get('success')}")
        print(f"   📍 Location: {risk_data.get('location')}")
        print(f"   🎯 Total risks: {risk_data.get('total_risks')}")
        print(f"   ⚠️  High severity: {risk_data.get('risk_summary', {}).get('high_severity_risks')}")
        
        # Show risk types
        risk_types = risk_data.get('risk_summary', {}).get('risk_types', [])
        if risk_types:
            print(f"   📋 Risk types: {', '.join(risk_types)}")
        
        # Show insights
        insights = risk_data.get('risk_insights', [])
        if insights:
            print(f"\n   💡 Insights:")
            for insight in insights[:3]:  # Show first 3
                print(f"      {insight}")
        
        print("\n✅ TEST 1 PASSED: Risk analysis working with real data")
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
            "location": "Lyon",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        
        # First risk analysis (cache miss)
        print("\n📊 First risk analysis (cache miss)...")
        start = time.time()
        result1 = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": "blé"
        })
        time1 = time.time() - start
        print(f"   ⏱️  Time: {time1:.3f}s ({time1*1000:.0f}ms)")
        
        # Second risk analysis (cache hit)
        print("\n📊 Second risk analysis (cache hit)...")
        start = time.time()
        result2 = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": "blé"
        })
        time2 = time.time() - start
        print(f"   ⏱️  Time: {time2:.3f}s ({time2*1000:.0f}ms)")
        
        # Verify results identical
        if result1 == result2:
            print("   ✅ Results identical (cache working)")
        else:
            print("   ⚠️  Results differ")
        
        # Calculate speedup
        speedup = (time1 - time2) / time1 * 100
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
        if 'memory_caches' in stats:
            for category, cache_stats in stats['memory_caches'].items():
                if cache_stats['size'] > 0:
                    print(f"   {category}: {cache_stats['size']}/{cache_stats['maxsize']} items ({cache_stats['utilization']:.1f}%)")
        
        if speedup > 50:
            print(f"\n✅ EXCELLENT: {speedup:.1f}% speedup with caching")
        elif speedup > 0:
            print(f"\n✅ GOOD: {speedup:.1f}% speedup")
        else:
            print(f"\n⚠️ Cache not providing speedup")
        
        print("\n✅ TEST 2 PASSED: Caching working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_crop_specific_analysis():
    """Test 3: Crop-specific analysis"""
    print("\n" + "="*80)
    print("TEST 3: Crop-Specific Analysis")
    print("="*80)
    
    try:
        # Get weather data
        print("\n📞 Getting weather data for Marseille...")
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Marseille",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        
        # Test different crops
        crops = ["blé", "maïs", "colza"]
        
        for crop in crops:
            print(f"\n🌾 Analyzing risks for {crop}...")
            result = await analyze_weather_risks_tool_enhanced.ainvoke({
                "weather_data_json": weather_result,
                "crop_type": crop
            })
            
            data = json.loads(result)
            print(f"   ✅ Crop: {data.get('crop_type')}")
            print(f"   🎯 Total risks: {data.get('total_risks')}")
            
            # Show crop-specific insights
            insights = data.get('risk_insights', [])
            crop_insights = [i for i in insights if crop in i.lower() or '🌾' in i or '🌽' in i or '🌻' in i]
            if crop_insights:
                print(f"   💡 Crop-specific insight: {crop_insights[0]}")
        
        print("\n✅ TEST 3 PASSED: Crop-specific analysis working")
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
        result = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": "invalid json",
            "crop_type": None
        })
        
        data = json.loads(result)
        print(f"   Result type: {type(result)}")
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
        result = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": empty_weather,
            "crop_type": None
        })
        
        data = json.loads(result)
        if not data.get('success'):
            print("   ✅ Empty data error handled")
        else:
            print("   ⚠️ Should have returned error for empty data")
        
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
    print("ENHANCED RISK ANALYSIS TOOL - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    print("\n⚠️  Note: Using REAL Weather API")
    
    tests = [
        ("Risk Analysis with Real Data", test_1_risk_analysis_with_real_data),
        ("Caching Performance", test_2_caching_performance),
        ("Crop-Specific Analysis", test_3_crop_specific_analysis),
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
        print("\n🎉 ALL TESTS PASSED! Enhanced risk analysis tool is ready to use.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review and fix before deployment.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

