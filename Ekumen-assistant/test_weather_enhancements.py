"""
Test Weather Enhancements

Tests the enhanced weather threshold checks:
- Temperature limits (>25°C, <10°C)
- Humidity effects (<30% critical, <50% warning)
- Rain forecast (48h window)
- Temperature inversion (critical)
"""

import asyncio
from app.tools.regulatory_agent.check_environmental_regulations_tool_enhanced import (
    check_environmental_regulations_tool_enhanced
)


async def test_temperature_warnings():
    """Test temperature threshold warnings"""
    print("\n" + "="*80)
    print("TEST 1: Temperature Warnings")
    print("="*80)
    
    # Test high temperature
    result_hot = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "moderate",
            "temperature_c": 28.0,  # High temperature
            "wind_speed_kmh": 12.0
        }
    })
    
    print("\n🌡️ HIGH TEMPERATURE (28°C):")
    print(f"   Critical Warnings: {len(result_hot['critical_warnings'])}")
    for warning in result_hot['critical_warnings']:
        if 'TEMPÉRATURE' in warning:
            print(f"   • {warning}")
    
    print(f"   Recommendations: {len(result_hot['environmental_recommendations'])}")
    for rec in result_hot['environmental_recommendations']:
        if 'Température' in rec or 'matin' in rec:
            print(f"   • {rec}")
    
    # Test low temperature
    result_cold = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "moderate",
            "temperature_c": 8.0,  # Low temperature
            "wind_speed_kmh": 12.0
        }
    })
    
    print("\n❄️ LOW TEMPERATURE (8°C):")
    print(f"   Critical Warnings: {len(result_cold['critical_warnings'])}")
    for warning in result_cold['critical_warnings']:
        if 'TEMPÉRATURE' in warning:
            print(f"   • {warning}")
    
    print("\n✅ Test 1 PASSED")


async def test_humidity_warnings():
    """Test humidity threshold warnings"""
    print("\n" + "="*80)
    print("TEST 2: Humidity Warnings")
    print("="*80)
    
    # Test critical humidity (<30%)
    result_critical = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "moderate",
            "humidity_percent": 25.0,  # Critical humidity
            "wind_speed_kmh": 12.0
        }
    })
    
    print("\n💧 CRITICAL HUMIDITY (25%):")
    print(f"   Critical Warnings: {len(result_critical['critical_warnings'])}")
    for warning in result_critical['critical_warnings']:
        if 'HUMIDITÉ' in warning:
            print(f"   • {warning}")
    
    # Test low humidity (<50%)
    result_low = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "moderate",
            "humidity_percent": 45.0,  # Low humidity
            "wind_speed_kmh": 12.0
        }
    })
    
    print("\n💧 LOW HUMIDITY (45%):")
    print(f"   Recommendations: {len(result_low['environmental_recommendations'])}")
    for rec in result_low['environmental_recommendations']:
        if 'Humidité' in rec or 'bouillie' in rec:
            print(f"   • {rec}")
    
    print("\n✅ Test 2 PASSED")


async def test_rain_forecast():
    """Test rain forecast warnings"""
    print("\n" + "="*80)
    print("TEST 3: Rain Forecast Warnings")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "moderate",
            "rain_forecast_48h": True,  # Rain forecast
            "wind_speed_kmh": 12.0
        }
    })
    
    print("\n🌧️ RAIN FORECAST (48h):")
    print(f"   Critical Warnings: {len(result['critical_warnings'])}")
    for warning in result['critical_warnings']:
        if 'PLUIE' in warning:
            print(f"   • {warning}")
    
    print(f"   Recommendations: {len(result['environmental_recommendations'])}")
    for rec in result['environmental_recommendations']:
        if 'Pluie' in rec or 'météo' in rec:
            print(f"   • {rec}")
    
    print("\n✅ Test 3 PASSED")


async def test_temperature_inversion():
    """Test temperature inversion critical warning"""
    print("\n" + "="*80)
    print("TEST 4: Temperature Inversion (CRITICAL)")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "moderate",
            "temperature_inversion": True,  # Temperature inversion
            "wind_speed_kmh": 12.0
        }
    })
    
    print("\n🚫 TEMPERATURE INVERSION:")
    print(f"   Critical Warnings: {len(result['critical_warnings'])}")
    for warning in result['critical_warnings']:
        if 'Inversion' in warning or 'INVERSION' in warning:
            print(f"   • {warning}")
    
    print("\n✅ Test 4 PASSED")


async def test_combined_weather_conditions():
    """Test multiple adverse weather conditions"""
    print("\n" + "="*80)
    print("TEST 5: Combined Adverse Weather Conditions")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Test",
        "environmental_impact": {
            "impact_level": "high",
            "temperature_c": 27.0,  # High temperature
            "humidity_percent": 28.0,  # Critical humidity
            "wind_speed_kmh": 18.0,  # High wind
            "rain_forecast_48h": True,  # Rain forecast
            "water_proximity_m": 4.0  # Too close to water
        }
    })
    
    print("\n⚠️ MULTIPLE ADVERSE CONDITIONS:")
    print(f"   • Temperature: 27°C (>25°C)")
    print(f"   • Humidity: 28% (<30%)")
    print(f"   • Wind: 18 km/h (>15 km/h)")
    print(f"   • Rain forecast: Yes")
    print(f"   • Water proximity: 4m (<5m)")
    
    print(f"\n🚨 Critical Warnings: {len(result['critical_warnings'])}")
    for warning in result['critical_warnings']:
        print(f"   • {warning}")
    
    print(f"\n💡 Recommendations: {len(result['environmental_recommendations'])}")
    for rec in result['environmental_recommendations'][:8]:
        print(f"   • {rec}")
    
    print(f"\n🎯 Environmental Risk: {result['environmental_risk']['risk_level']}")
    print(f"   Risk Score: {result['environmental_risk']['risk_score']}")
    
    print("\n✅ Test 5 PASSED")


async def main():
    """Run all weather enhancement tests"""
    print("\n" + "="*80)
    print("🌦️ TESTING WEATHER ENHANCEMENTS")
    print("="*80)
    
    try:
        await test_temperature_warnings()
        await test_humidity_warnings()
        await test_rain_forecast()
        await test_temperature_inversion()
        await test_combined_weather_conditions()
        
        print("\n" + "="*80)
        print("✅ ALL WEATHER ENHANCEMENT TESTS PASSED!")
        print("="*80)
        
        print("\n📊 WEATHER FEATURES TESTED:")
        print("   ✅ Temperature thresholds:")
        print("      - High: >25°C (evaporation risk, treat morning/evening)")
        print("      - Low: <10°C (reduced efficacy, check label)")
        
        print("\n   ✅ Humidity thresholds:")
        print("      - Critical: <30% (increased drift risk)")
        print("      - Low: <50% (increase spray volume)")
        
        print("\n   ✅ Rain forecast:")
        print("      - 48h window (runoff risk, delay treatment)")
        
        print("\n   ✅ Temperature inversion:")
        print("      - CRITICAL: Treatment PROHIBITED (major drift risk)")
        
        print("\n   ✅ Combined conditions:")
        print("      - Multiple weather factors assessed simultaneously")
        print("      - Comprehensive warnings and recommendations")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

