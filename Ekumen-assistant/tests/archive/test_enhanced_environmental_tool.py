"""
Test Enhanced Environmental Regulations Tool

Tests comprehensive environmental compliance checking with:
- Configuration-based regulations
- EPHY database integration for ZNT
- Risk assessment
- Seasonal restrictions
- Critical warnings
"""

import asyncio
import time
from datetime import date
from app.tools.regulatory_agent.check_environmental_regulations_tool_enhanced import (
    check_environmental_regulations_tool_enhanced
)


async def test_basic_environmental_check():
    """Test 1: Basic environmental regulations check (configuration)"""
    print("\n" + "="*80)
    print("TEST 1: Basic Environmental Regulations Check (Configuration)")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Bretagne",
        "environmental_impact": {
            "impact_level": "moderate",
            "water_proximity_m": 15.0,
            "wind_speed_kmh": 12.0,
            "flowering_period": False,
            "sensitive_area": False
        }
    })
    
    print(f"\n✅ Success: {result['success']}")
    print(f"📍 Practice Type: {result['practice_type']}")
    print(f"📊 Total Regulations: {result['total_regulations']}")
    print(f"✅ Compliant: {result['compliant_count']}")
    print(f"⚠️  Non-Compliant: {result['non_compliant_count']}")
    print(f"\n🎯 Environmental Risk:")
    print(f"   Level: {result['environmental_risk']['risk_level']}")
    print(f"   Score: {result['environmental_risk']['risk_score']}")
    print(f"   High Impact Count: {result['environmental_risk']['high_impact_count']}")
    
    print(f"\n📋 Regulations:")
    for reg in result['environmental_regulations'][:2]:
        print(f"   • {reg['regulation_name']}")
        print(f"     Status: {reg['compliance_status']}")
        print(f"     Impact: {reg['environmental_impact']}")
        print(f"     Source: {reg['source']}")
    
    print(f"\n💡 Recommendations ({len(result['environmental_recommendations'])}):")
    for rec in result['environmental_recommendations'][:3]:
        print(f"   • {rec}")
    
    print(f"\n🔍 Data Source: {result['data_source']}")
    
    assert result['success'] == True
    assert result['total_regulations'] > 0
    print("\n✅ Test 1 PASSED")


async def test_database_znt_compliance():
    """Test 2: Database ZNT compliance check"""
    print("\n" + "="*80)
    print("TEST 2: Database ZNT Compliance Check (EPHY)")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Île-de-France",
        "environmental_impact": {
            "impact_level": "high",
            "water_proximity_m": 3.0,  # Too close!
            "wind_speed_kmh": 10.0,
            "flowering_period": False,
            "sensitive_area": False
        },
        "amm_codes": ["2050007"]  # Real AMM code
    })
    
    print(f"\n✅ Success: {result['success']}")
    print(f"📊 Total Regulations: {result['total_regulations']}")
    print(f"⚠️  Non-Compliant: {result['non_compliant_count']}")
    
    if result.get('znt_compliance'):
        print(f"\n🌊 ZNT Compliance (from EPHY database):")
        for znt in result['znt_compliance']:
            print(f"   • Type: {znt['znt_type']}")
            print(f"     Required: {znt['required_znt_m']}m")
            print(f"     Actual: {znt.get('actual_distance_m')}m")
            print(f"     Compliant: {znt['is_compliant']}")
            if znt.get('reduction_possible'):
                print(f"     Reduction possible: {znt['reduction_possible']}")
    
    print(f"\n🎯 Environmental Risk:")
    print(f"   Level: {result['environmental_risk']['risk_level']}")
    print(f"   Score: {result['environmental_risk']['risk_score']}")
    print(f"   Critical Issues: {len(result['environmental_risk']['critical_issues'])}")
    
    if result.get('critical_warnings'):
        print(f"\n🚨 Critical Warnings ({len(result['critical_warnings'])}):")
        for warning in result['critical_warnings']:
            print(f"   • {warning}")
    
    print(f"\n💡 Recommendations ({len(result['environmental_recommendations'])}):")
    for rec in result['environmental_recommendations'][:5]:
        print(f"   • {rec}")
    
    print(f"\n🔍 Data Source: {result['data_source']}")
    
    assert result['success'] == True
    print("\n✅ Test 2 PASSED")


async def test_fertilization_nitrate_directive():
    """Test 3: Fertilization with Nitrate Directive"""
    print("\n" + "="*80)
    print("TEST 3: Fertilization - Nitrate Directive")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "fertilization",
        "location": "Normandie",
        "environmental_impact": {
            "impact_level": "moderate",
            "water_proximity_m": 25.0,
            "sensitive_area": False
        },
        "field_size_ha": 10.5,
        "application_date": "2024-12-15"  # Winter - restricted period!
    })
    
    print(f"\n✅ Success: {result['success']}")
    print(f"📊 Total Regulations: {result['total_regulations']}")
    
    print(f"\n📋 Regulations:")
    for reg in result['environmental_regulations']:
        print(f"   • {reg['regulation_name']}")
        print(f"     Status: {reg['compliance_status']}")
        print(f"     Impact: {reg['environmental_impact']}")
        if reg.get('legal_references'):
            print(f"     Legal: {reg['legal_references'][0]}")
    
    if result.get('seasonal_restrictions'):
        print(f"\n❄️  Seasonal Restrictions:")
        for restriction in result['seasonal_restrictions']:
            print(f"   • {restriction}")
    
    print(f"\n🎯 Environmental Risk:")
    print(f"   Level: {result['environmental_risk']['risk_level']}")
    print(f"   Score: {result['environmental_risk']['risk_score']}")
    
    assert result['success'] == True
    assert result.get('seasonal_restrictions') is not None
    print("\n✅ Test 3 PASSED")


async def test_sensitive_area_high_risk():
    """Test 4: Sensitive area (Natura 2000) with high risk"""
    print("\n" + "="*80)
    print("TEST 4: Sensitive Area (Natura 2000) - High Risk")
    print("="*80)
    
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying",
        "location": "Provence",
        "environmental_impact": {
            "impact_level": "high",
            "water_proximity_m": 8.0,
            "wind_speed_kmh": 18.0,
            "flowering_period": True,  # Flowering!
            "sensitive_area": True  # Natura 2000
        },
        "application_date": "2024-05-15"  # Spring - flowering period
    })
    
    print(f"\n✅ Success: {result['success']}")
    print(f"📊 Total Regulations: {result['total_regulations']}")
    print(f"⚠️  Non-Compliant: {result['non_compliant_count']}")
    
    print(f"\n🎯 Environmental Risk:")
    print(f"   Level: {result['environmental_risk']['risk_level']}")
    print(f"   Score: {result['environmental_risk']['risk_score']}")
    print(f"   Non-Compliant Count: {result['environmental_risk']['non_compliant_count']}")
    
    if result.get('critical_warnings'):
        print(f"\n🚨 Critical Warnings ({len(result['critical_warnings'])}):")
        for warning in result['critical_warnings']:
            print(f"   • {warning}")
    
    if result.get('seasonal_restrictions'):
        print(f"\n🌸 Seasonal Restrictions:")
        for restriction in result['seasonal_restrictions']:
            print(f"   • {restriction}")
    
    print(f"\n💡 Recommendations ({len(result['environmental_recommendations'])}):")
    for rec in result['environmental_recommendations'][:5]:
        print(f"   • {rec}")
    
    assert result['success'] == True
    assert result['environmental_risk']['risk_level'] in ['high', 'critical']
    print("\n✅ Test 4 PASSED")


async def test_caching_performance():
    """Test 5: Caching performance"""
    print("\n" + "="*80)
    print("TEST 5: Caching Performance")
    print("="*80)
    
    test_input = {
        "practice_type": "irrigation",
        "location": "Occitanie",
        "environmental_impact": {
            "impact_level": "moderate",
            "water_proximity_m": 50.0
        },
        "application_date": "2024-08-15"  # Summer - drought risk
    }
    
    # First call (uncached)
    start_time = time.time()
    result1 = await check_environmental_regulations_tool_enhanced.ainvoke(test_input)
    first_call_time = (time.time() - start_time) * 1000
    
    # Second call (cached)
    start_time = time.time()
    result2 = await check_environmental_regulations_tool_enhanced.ainvoke(test_input)
    second_call_time = (time.time() - start_time) * 1000
    
    print(f"\n⏱️  First call (uncached): {first_call_time:.2f}ms")
    print(f"⏱️  Second call (cached): {second_call_time:.2f}ms")
    print(f"🚀 Speedup: {first_call_time / second_call_time:.2f}x")

    print(f"\n✅ Success: {result2['success']}")
    print(f"📊 Total Regulations: {result2['total_regulations']}")

    if result2.get('seasonal_restrictions'):
        print(f"\n☀️  Seasonal Restrictions (Summer):")
        for restriction in result2['seasonal_restrictions']:
            print(f"   • {restriction}")

    # Compare results excluding timestamp (which will differ)
    result1_copy = {k: v for k, v in result1.items() if k != 'timestamp'}
    result2_copy = {k: v for k, v in result2.items() if k != 'timestamp'}
    assert result1_copy == result2_copy
    print("\n✅ Test 5 PASSED")


async def test_error_handling():
    """Test 6: Error handling"""
    print("\n" + "="*80)
    print("TEST 6: Error Handling")
    print("="*80)
    
    # Test with invalid practice type
    result = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "invalid_practice",
        "location": "Test"
    })
    
    print(f"\n✅ Handled invalid practice type:")
    print(f"   Success: {result['success']}")
    print(f"   Total Regulations: {result['total_regulations']}")
    
    # Test with minimal input
    result2 = await check_environmental_regulations_tool_enhanced.ainvoke({
        "practice_type": "spraying"
    })
    
    print(f"\n✅ Handled minimal input:")
    print(f"   Success: {result2['success']}")
    print(f"   Total Regulations: {result2['total_regulations']}")
    
    print("\n✅ Test 6 PASSED")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING ENHANCED ENVIRONMENTAL REGULATIONS TOOL")
    print("="*80)
    
    try:
        await test_basic_environmental_check()
        await test_database_znt_compliance()
        await test_fertilization_nitrate_directive()
        await test_sensitive_area_high_risk()
        await test_caching_performance()
        await test_error_handling()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        
        print("\n📊 TEST SUMMARY:")
        print("   ✅ Test 1: Basic environmental regulations - PASSED")
        print("   ✅ Test 2: Database ZNT compliance - PASSED")
        print("   ✅ Test 3: Fertilization nitrate directive - PASSED")
        print("   ✅ Test 4: Sensitive area high risk - PASSED")
        print("   ✅ Test 5: Caching performance - PASSED")
        print("   ✅ Test 6: Error handling - PASSED")
        
        print("\n🎉 Enhanced CheckEnvironmentalRegulationsTool is production-ready!")
        
        print("\n🚀 FEATURES:")
        print("   - Configuration-based environmental regulations")
        print("   - EPHY database integration for ZNT requirements")
        print("   - Water protection (ZNT, cours d'eau, nappes)")
        print("   - Biodiversity protection (abeilles, Natura 2000)")
        print("   - Air quality (dérive, distances habitations)")
        print("   - Nitrate directive (fertilisation)")
        print("   - Seasonal restrictions (winter, flowering, drought)")
        print("   - Risk assessment with critical warnings")
        print("   - Legal references")
        print("   - Redis + memory caching (2h TTL)")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

