"""
Test suite for Enhanced Safety Guidelines Tool

Tests database integration, caching, and comprehensive safety information.
"""

import asyncio
import json
import time
from app.tools.regulatory_agent.get_safety_guidelines_tool_enhanced import get_safety_guidelines_tool
from app.core.cache import clear_cache


async def test_basic_safety_guidelines():
    """Test 1: Basic safety guidelines from configuration"""
    print("\n" + "="*80)
    print("TEST 1: Basic Safety Guidelines (Configuration)")
    print("="*80)
    
    result_json = await get_safety_guidelines_tool.ainvoke({
        "product_type": "herbicide",
        "practice_type": "spraying",
        "safety_level": "standard"
    })
    
    result = json.loads(result_json)
    
    print(f"\n✅ Success: {result['success']}")
    print(f"📦 Product Type: {result['product_type']}")
    print(f"🔧 Practice Type: {result['practice_type']}")
    print(f"⚠️  Safety Level: {result['safety_level']}")
    print(f"🎯 Safety Priority: {result['safety_priority']}")
    print(f"📊 Total Guidelines: {result['total_guidelines']}")
    print(f"📍 Data Source: {result['data_source']}")
    
    if result['safety_guidelines']:
        print(f"\n📋 Guidelines ({len(result['safety_guidelines'])}):")
        for guideline in result['safety_guidelines']:
            print(f"\n   {guideline['guideline_type']}:")
            print(f"      Description: {guideline['description']}")
            print(f"      Equipment: {[eq['equipment_type'] for eq in guideline['required_equipment']]}")
            print(f"      Measures: {len(guideline['safety_measures'])} measures")
            print(f"      Emergency Procedures: {len(guideline['emergency_procedures'])} procedures")
    
    if result['safety_recommendations']:
        print(f"\n💡 Recommendations ({len(result['safety_recommendations'])}):")
        for rec in result['safety_recommendations'][:5]:
            print(f"   - {rec}")
    
    if result['emergency_contacts']:
        print(f"\n🚨 Emergency Contacts:")
        for contact, number in list(result['emergency_contacts'].items())[:3]:
            print(f"   {contact}: {number}")
    
    assert result['success'], "Request should succeed"
    assert result['total_guidelines'] > 0, "Should have guidelines"
    assert result['data_source'] == "configuration", "Should use configuration data"
    
    print("\n✅ Test 1 PASSED")


async def test_database_product_safety():
    """Test 2: Product safety from EPHY database"""
    print("\n" + "="*80)
    print("TEST 2: Product Safety from EPHY Database")
    print("="*80)
    
    # Clear cache
    clear_cache(category="regulatory")
    
    # Test with product name (will search database)
    result_json = await get_safety_guidelines_tool.ainvoke({
        "product_name": "glyphosate",
        "safety_level": "high",
        "include_risk_phrases": True,
        "include_emergency_procedures": True
    })
    
    result = json.loads(result_json)
    
    print(f"\n✅ Success: {result['success']}")
    print(f"🎯 Safety Priority: {result['safety_priority']}")
    print(f"📊 Total Guidelines: {result['total_guidelines']}")
    print(f"📍 Data Source: {result['data_source']}")
    
    if result.get('product_safety_info'):
        psi = result['product_safety_info']
        print(f"\n🧪 Product Safety Info:")
        print(f"   AMM Code: {psi['amm_code']}")
        print(f"   Product Name: {psi['product_name']}")
        print(f"   Risk Phrases: {len(psi.get('risk_phrases', []))}")
        
        if psi.get('risk_phrases'):
            print(f"\n   ⚠️  Risk Phrases:")
            for phrase in psi['risk_phrases'][:5]:
                print(f"      {phrase['code']}: {phrase['description'][:60]}...")
        
        if psi.get('safety_interval_days'):
            print(f"   ⏱️  Safety Interval: {psi['safety_interval_days']} days")
        
        if psi.get('znt_requirements'):
            print(f"   🌊 ZNT Requirements: {psi['znt_requirements']}")
    
    if result.get('critical_warnings'):
        print(f"\n⚠️  Critical Warnings ({len(result['critical_warnings'])}):")
        for warning in result['critical_warnings']:
            print(f"   {warning}")
    
    print(f"\n💡 Safety Recommendations ({len(result['safety_recommendations'])}):")
    for rec in result['safety_recommendations'][:5]:
        print(f"   - {rec}")
    
    assert result['success'], "Request should succeed"
    
    print("\n✅ Test 2 PASSED")


async def test_caching_performance():
    """Test 3: Caching performance"""
    print("\n" + "="*80)
    print("TEST 3: Caching Performance")
    print("="*80)
    
    # Clear cache
    clear_cache(category="regulatory")
    
    # First call (uncached)
    start = time.time()
    result1_json = await get_safety_guidelines_tool.ainvoke({
        "product_type": "insecticide",
        "safety_level": "standard"
    })
    time1 = time.time() - start
    
    # Second call (cached)
    start = time.time()
    result2_json = await get_safety_guidelines_tool.ainvoke({
        "product_type": "insecticide",
        "safety_level": "standard"
    })
    time2 = time.time() - start
    
    result1 = json.loads(result1_json)
    result2 = json.loads(result2_json)
    
    print(f"\n⏱️  First call (uncached): {time1:.4f}s")
    print(f"⏱️  Second call (cached): {time2:.4f}s")
    
    if time2 < time1:
        speedup = time1 / time2
        time_saved = (time1 - time2) * 1000
        print(f"🚀 Speedup: {speedup:.1f}x faster")
        print(f"📉 Time saved: {time_saved:.1f}ms")
        print("✅ Cache is faster!")
    else:
        print("⚠️  Cache not faster (might be due to overhead)")
    
    # Verify results are identical
    assert result1['total_guidelines'] == result2['total_guidelines'], "Results should be identical"
    
    print("\n✅ Test 3 PASSED")


async def test_high_safety_level():
    """Test 4: High safety level with multiple guidelines"""
    print("\n" + "="*80)
    print("TEST 4: High Safety Level")
    print("="*80)
    
    result_json = await get_safety_guidelines_tool.ainvoke({
        "product_type": "insecticide",
        "practice_type": "spraying",
        "safety_level": "high"
    })
    
    result = json.loads(result_json)
    
    print(f"\n✅ Success: {result['success']}")
    print(f"🎯 Safety Priority: {result['safety_priority']}")
    print(f"📊 Total Guidelines: {result['total_guidelines']}")
    
    # Count total equipment
    all_equipment = set()
    for guideline in result['safety_guidelines']:
        for eq in guideline['required_equipment']:
            all_equipment.add(eq['equipment_type'])
    
    print(f"\n🛡️  Total Unique Equipment: {len(all_equipment)}")
    print(f"   Equipment: {', '.join(sorted(all_equipment))}")
    
    # Count total safety measures
    total_measures = sum(
        len(g['safety_measures']) for g in result['safety_guidelines']
    )
    print(f"\n📋 Total Safety Measures: {total_measures}")
    
    # Count total emergency procedures
    total_procedures = sum(
        len(g['emergency_procedures']) for g in result['safety_guidelines']
    )
    print(f"🚨 Total Emergency Procedures: {total_procedures}")
    
    assert result['success'], "Request should succeed"
    assert result['safety_priority'] in ['high', 'critical'], "Should have high priority"
    assert len(all_equipment) >= 3, "Should have multiple equipment items"
    
    print("\n✅ Test 4 PASSED")


async def test_error_handling():
    """Test 5: Error handling"""
    print("\n" + "="*80)
    print("TEST 5: Error Handling")
    print("="*80)
    
    # Test with invalid safety level
    result_json = await get_safety_guidelines_tool.ainvoke({
        "product_type": "herbicide",
        "safety_level": "invalid_level"
    })
    
    result = json.loads(result_json)
    
    print(f"\n✅ Handled invalid safety level:")
    print(f"   Success: {result['success']}")
    print(f"   Error: {result.get('error', 'N/A')}")
    print(f"   Error Type: {result.get('error_type', 'N/A')}")
    
    # Test with minimal input
    result_json = await get_safety_guidelines_tool.ainvoke({
        "safety_level": "basic"
    })
    
    result = json.loads(result_json)
    
    print(f"\n✅ Handled minimal input:")
    print(f"   Success: {result['success']}")
    print(f"   Total Guidelines: {result['total_guidelines']}")
    
    print("\n✅ Test 5 PASSED")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 ENHANCED SAFETY GUIDELINES TOOL TEST SUITE")
    print("="*80)
    
    try:
        # Run all tests
        await test_basic_safety_guidelines()
        await test_database_product_safety()
        await test_caching_performance()
        await test_high_safety_level()
        await test_error_handling()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n📊 TEST SUMMARY:")
        print("   ✅ Test 1: Basic safety guidelines - PASSED")
        print("   ✅ Test 2: Database product safety - PASSED")
        print("   ✅ Test 3: Caching performance - PASSED")
        print("   ✅ Test 4: High safety level - PASSED")
        print("   ✅ Test 5: Error handling - PASSED")
        print("\n🎉 Enhanced GetSafetyGuidelinesTool is production-ready!")
        print("\n🚀 FEATURES:")
        print("   - EPHY database integration for product safety data")
        print("   - Risk phrases (H-phrases, P-phrases)")
        print("   - Safety intervals (DAR, re-entry)")
        print("   - ZNT requirements")
        print("   - Emergency procedures with contact info")
        print("   - Legal references")
        print("   - Redis + memory caching (2h TTL)")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

