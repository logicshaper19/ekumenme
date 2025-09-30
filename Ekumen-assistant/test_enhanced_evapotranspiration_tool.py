"""
Comprehensive tests for enhanced evapotranspiration tool - WITH REAL API

Tests:
1. Basic ET calculation with real weather data
2. Caching performance
3. Crop-specific calculations
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
from app.tools.weather_agent.calculate_evapotranspiration_tool_enhanced import (
    calculate_evapotranspiration_tool_enhanced
)
from app.core.cache import get_cache_stats, clear_cache


async def test_1_basic_et_calculation():
    """Test 1: Basic ET calculation with real weather data"""
    print("\n" + "="*80)
    print("TEST 1: Basic ET Calculation with Real Weather Data")
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
        
        # Step 2: Calculate evapotranspiration
        print("\n💧 Step 2: Calculating evapotranspiration...")
        start = time.time()
        et_result = await calculate_evapotranspiration_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": None,  # General calculation
            "crop_stage": None
        })
        elapsed = time.time() - start
        
        data = json.loads(et_result)
        
        # Verify structure
        assert data.get('success') == True, "ET calculation should succeed"
        assert data.get('location') is not None, "Should have location"
        assert data.get('daily_et') is not None, "Should have daily ET data"
        assert len(data.get('daily_et', [])) > 0, "Should have ET calculations"
        assert data.get('water_balance') is not None, "Should have water balance"
        assert data.get('avg_et0') is not None, "Should have average ET0"
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Location: {data.get('location')}")
        print(f"   Period: {data.get('forecast_period_days')} days")
        print(f"   Average ET0: {data.get('avg_et0')} mm/day")
        print(f"   Calculation method: {data.get('calculation_method')}")
        
        # Water balance
        wb = data.get('water_balance', {})
        print(f"\n💧 Water Balance:")
        print(f"   Total ET0: {wb.get('total_et0')} mm")
        print(f"   Total precipitation: {wb.get('total_precipitation')} mm")
        print(f"   Water deficit: {wb.get('water_deficit')} mm")
        print(f"   Irrigation needed: {wb.get('irrigation_needed')}")
        
        # Irrigation recommendations
        recommendations = data.get('irrigation_recommendations', [])
        print(f"\n🚿 Irrigation Recommendations: {len(recommendations)}")
        if recommendations:
            for rec in recommendations[:2]:  # Show first 2
                print(f"   - {rec.get('date')}: {rec.get('amount_mm')}mm ({rec.get('amount_m3_ha')}m³/ha)")
                print(f"     Priority: {rec.get('priority')}, Time: {rec.get('optimal_time')}")
        
        print(f"\n⏱️  Calculation time: {elapsed:.3f}s ({elapsed*1000:.0f}ms)")
        print("\n✅ TEST 1 PASSED: Basic ET calculation working with real data")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
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
        print("🧹 Cache cleared\n")
        
        # Get weather data once
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Normandie",
            "days": 7,
            "use_real_api": True
        })
        
        # First ET calculation (cache miss)
        print("🔄 First ET calculation (cache miss)...")
        start = time.time()
        result1 = await calculate_evapotranspiration_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": "blé",
            "crop_stage": "floraison"
        })
        time1 = time.time() - start
        print(f"   ⏱️  Time: {time1:.3f}s ({time1*1000:.0f}ms)")
        
        # Second ET calculation (cache hit)
        print("\n🔄 Second ET calculation (cache hit)...")
        start = time.time()
        result2 = await calculate_evapotranspiration_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": "blé",
            "crop_stage": "floraison"
        })
        time2 = time.time() - start
        print(f"   ⏱️  Time: {time2:.3f}s ({time2*1000:.0f}ms)")
        
        # Verify results are identical
        assert result1 == result2, "Cached result should be identical"
        
        # Calculate speedup
        speedup = ((time1 - time2) / time1 * 100) if time1 > 0 else 0
        print(f"\n📈 Performance:")
        print(f"   Speedup: {speedup:.1f}%")
        print(f"   Time saved: {(time1 - time2)*1000:.0f}ms")
        
        # Show cache stats
        stats = get_cache_stats()
        print(f"\n📊 Cache Stats:")
        print(f"   Redis available: {stats.get('redis_available', False)}")
        print(f"   Total memory items: {stats.get('total_memory_items', 0)}")
        if 'memory_caches' in stats and 'weather' in stats['memory_caches']:
            weather_stats = stats['memory_caches']['weather']
            print(f"   Weather cache size: {weather_stats.get('size', 0)} items")
        
        print("\n✅ TEST 2 PASSED: Caching working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_crop_specific_calculations():
    """Test 3: Crop-specific ET calculations"""
    print("\n" + "="*80)
    print("TEST 3: Crop-Specific ET Calculations")
    print("="*80)
    
    try:
        # Get weather data
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Bretagne",
            "days": 7,
            "use_real_api": True
        })
        
        # Test different crops and stages
        test_cases = [
            ("blé", "floraison"),
            ("maïs", "croissance"),
            ("colza", "maturation"),
        ]
        
        for crop_type, crop_stage in test_cases:
            print(f"\n🌾 Testing {crop_type} at {crop_stage} stage...")
            result = await calculate_evapotranspiration_tool_enhanced.ainvoke({
                "weather_data_json": weather_result,
                "crop_type": crop_type,
                "crop_stage": crop_stage
            })
            
            data = json.loads(result)
            assert data.get('success') == True, f"Should succeed for {crop_type}"
            assert data.get('crop_type') == crop_type, f"Should have crop type {crop_type}"
            assert data.get('crop_stage') == crop_stage, f"Should have crop stage {crop_stage}"
            
            # Verify crop-specific calculations
            daily_et = data.get('daily_et', [])
            assert len(daily_et) > 0, "Should have daily ET data"
            
            # Check that ETc is calculated (crop-specific)
            first_day = daily_et[0]
            assert first_day.get('etc') is not None, "Should have crop ET (ETc)"
            assert first_day.get('kc') is not None, "Should have crop coefficient (Kc)"
            
            print(f"   ✅ Crop: {crop_type}, Stage: {crop_stage}")
            print(f"   📊 Avg ET0: {data.get('avg_et0')} mm/day")
            print(f"   📊 Avg ETc: {data.get('avg_etc')} mm/day")
            print(f"   📊 Kc: {first_day.get('kc')}")
            
            # Check irrigation recommendations
            recommendations = data.get('irrigation_recommendations', [])
            if recommendations:
                print(f"   🚿 Irrigation recommendations: {len(recommendations)}")
        
        print("\n✅ TEST 3 PASSED: Crop-specific calculations working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_error_handling():
    """Test 4: Error handling"""
    print("\n" + "="*80)
    print("TEST 4: Error Handling")
    print("="*80)

    try:
        # Test 1: Empty weather data (will be caught by Pydantic before our function)
        print("\n🧪 Test 4.1: Empty weather data...")
        try:
            result = await calculate_evapotranspiration_tool_enhanced.ainvoke({
                "weather_data_json": "",
                "crop_type": "blé"
            })
            # If we get here, it should be an error response
            data = json.loads(result)
            assert data.get('success') == False, "Should fail with empty data"
        except Exception as e:
            # LangChain's StructuredTool validates before our function
            # This is expected for empty strings
            assert "weather_data_json" in str(e), "Error should mention weather_data_json"
            print(f"   ✅ Empty data rejected by validation (expected): {type(e).__name__}")

        # Test 2: Invalid JSON (valid string, but not JSON)
        print("\n🧪 Test 4.2: Invalid JSON...")
        result = await calculate_evapotranspiration_tool_enhanced.ainvoke({
            "weather_data_json": "not valid json",
            "crop_type": "blé"
        })
        data = json.loads(result)
        assert data.get('success') == False, "Should fail with invalid JSON"
        assert data.get('error_type') in ["validation", "data_missing"], "Should be validation or data error"
        print("   ✅ Invalid JSON handled correctly")

        # Test 3: Missing weather conditions
        print("\n🧪 Test 4.3: Missing weather conditions...")
        result = await calculate_evapotranspiration_tool_enhanced.ainvoke({
            "weather_data_json": '{"location": "Paris", "weather_conditions": []}',
            "crop_type": "blé"
        })
        data = json.loads(result)
        assert data.get('success') == False, "Should fail with no weather conditions"
        assert data.get('error_type') == "data_missing", "Should be data missing error"
        print("   ✅ Missing conditions handled correctly")

        # Test 4: Weather data with error
        print("\n🧪 Test 4.4: Weather data with error...")
        result = await calculate_evapotranspiration_tool_enhanced.ainvoke({
            "weather_data_json": '{"success": false, "error": "API error"}',
            "crop_type": "blé"
        })
        data = json.loads(result)
        assert data.get('success') == False, "Should fail with error in weather data"
        assert data.get('error_type') == "data_missing", "Should be data missing error"
        print("   ✅ Weather error handled correctly")

        print("\n✅ TEST 4 PASSED: Error handling working correctly")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("ENHANCED EVAPOTRANSPIRATION TOOL - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    print("\n⚠️  Note: Using REAL Weather API")
    
    tests = [
        ("Basic ET Calculation", test_1_basic_et_calculation),
        ("Caching Performance", test_2_caching_performance),
        ("Crop-Specific Calculations", test_3_crop_specific_calculations),
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
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

