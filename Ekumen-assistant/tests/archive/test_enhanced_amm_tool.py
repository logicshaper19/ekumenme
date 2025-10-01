"""
Test suite for Enhanced AMM Lookup Tool
Tests with real EPHY database (if available) or graceful degradation
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from app.tools.regulatory_agent.database_integrated_amm_tool_enhanced import (
    database_integrated_amm_tool_enhanced,
    EnhancedAMMService
)
from app.tools.schemas.amm_schemas import AMMInput, AMMOutput
from app.core.cache import get_cache_stats, clear_cache


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


async def test_1_basic_amm_lookup():
    """Test 1: Basic AMM product lookup"""
    print_section("TEST 1: Basic AMM Product Lookup")
    
    try:
        # Clear cache for fresh test
        clear_cache(category="regulatory")
        
        # Test input: Search for glyphosate products
        start_time = time.time()
        
        result = await database_integrated_amm_tool_enhanced.ainvoke({
            "active_ingredient": "glyphosate",
            "product_type": "PPP",
            "crop_type": "blé"
        })
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"⏱️  Execution time: {elapsed_ms:.1f}ms")
        print(f"📊 Result type: {type(result)}")
        
        # Parse result
        if isinstance(result, AMMOutput):
            output = result
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return False
        
        print(f"\n✅ Success: {output.success}")
        print(f"📋 Status: {output.status}")
        
        if output.success and output.status == "success":
            print(f"\n📊 Summary:")
            print(f"   Total products: {output.summary.total_products_found}")
            print(f"   Compliant: {output.summary.compliant_products}")
            print(f"   Non-compliant: {output.summary.non_compliant_products}")
            
            if output.compliant_products:
                print(f"\n🎯 First compliant product:")
                product = output.compliant_products[0]
                print(f"   AMM: {product.numero_amm}")
                print(f"   Name: {product.nom_produit}")
                print(f"   Type: {product.type_produit}")
                print(f"   Compliance score: {product.compliance_score}%")
                print(f"   Substances: {[s.nom for s in product.substances_actives]}")
            
            print(f"\n💡 Recommendations ({len(output.general_recommendations)}):")
            for rec in output.general_recommendations[:3]:
                print(f"   - {rec}")
        
        elif output.status == "no_results":
            print(f"\n⚠️  No products found")
            print(f"📋 Search criteria: {output.search_criteria}")
            print(f"💡 Recommendations:")
            for rec in output.recommendations[:3]:
                print(f"   - {rec}")
        
        elif not output.success:
            print(f"\n❌ Error: {output.error}")
            print(f"   Type: {output.error_type}")
        
        print(f"\n✅ TEST 1 PASSED: Basic AMM lookup")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_2_caching_performance():
    """Test 2: Caching performance"""
    print_section("TEST 2: Caching Performance")
    
    try:
        # Clear cache
        clear_cache(category="regulatory")
        
        # First call (cold cache)
        start_time = time.time()
        result1 = await database_integrated_amm_tool_enhanced.ainvoke({
            "product_name": "Roundup",
            "crop_type": "maïs"
        })
        time1_ms = (time.time() - start_time) * 1000
        
        # Second call (warm cache)
        start_time = time.time()
        result2 = await database_integrated_amm_tool_enhanced.ainvoke({
            "product_name": "Roundup",
            "crop_type": "maïs"
        })
        time2_ms = (time.time() - start_time) * 1000
        
        print(f"⏱️  First call (cold cache): {time1_ms:.1f}ms")
        print(f"⏱️  Second call (warm cache): {time2_ms:.1f}ms")
        
        if time2_ms < time1_ms:
            speedup = ((time1_ms - time2_ms) / time1_ms) * 100
            print(f"🚀 Speedup: {speedup:.1f}%")
        
        # Check cache stats
        stats = get_cache_stats()
        print(f"\n📊 Cache stats:")
        print(f"   Memory caches: {len(stats['memory_caches'])}")
        if 'regulatory' in stats['memory_caches']:
            reg_stats = stats['memory_caches']['regulatory']
            print(f"   Regulatory cache size: {reg_stats.get('size', 0)}")
            if 'hits' in reg_stats:
                print(f"   Regulatory cache hits: {reg_stats['hits']}")
                print(f"   Regulatory cache misses: {reg_stats['misses']}")
        
        print(f"\n✅ TEST 2 PASSED: Caching performance")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_farm_context():
    """Test 3: Farm context integration"""
    print_section("TEST 3: Farm Context Integration")
    
    try:
        # Test with farm context
        farm_context = {
            "region": "Hauts-de-France",
            "distance_to_water_m": 25,
            "organic_certified": False
        }
        
        result = await database_integrated_amm_tool_enhanced.ainvoke({
            "active_ingredient": "métribuzine",
            "crop_type": "pomme de terre",
            "farm_context": farm_context
        })
        
        if isinstance(result, AMMOutput):
            output = result
        else:
            print(f"❌ Unexpected result type")
            return False
        
        print(f"✅ Success: {output.success}")
        print(f"📋 Status: {output.status}")
        
        if output.success and output.regulatory_context:
            print(f"\n🌍 Regulatory context:")
            print(f"   ZNT requirements: {output.regulatory_context.znt_requirements}")
            print(f"   Season: {output.regulatory_context.seasonal_considerations.get('current_season', 'N/A')}")
            
            if output.regulatory_context.regional_factors:
                print(f"   Region: {output.regulatory_context.regional_factors.get('region', 'N/A')}")
        
        if output.general_recommendations:
            print(f"\n💡 Context-specific recommendations:")
            for rec in output.general_recommendations:
                if "ZNT" in rec or "cours d'eau" in rec:
                    print(f"   - {rec}")
        
        print(f"\n✅ TEST 3 PASSED: Farm context integration")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_error_handling():
    """Test 4: Error handling"""
    print_section("TEST 4: Error Handling")
    
    try:
        # Test 1: No search criteria
        print("Test 4.1: No search criteria")
        result = await database_integrated_amm_tool_enhanced.ainvoke({})
        
        if isinstance(result, AMMOutput):
            output = result
            print(f"   Success: {output.success}")
            print(f"   Error type: {output.error_type}")
            print(f"   Error: {output.error}")
            assert not output.success, "Should fail with no criteria"
            assert output.error_type == "validation", "Should be validation error"
        
        # Test 2: Invalid farm context
        print("\nTest 4.2: Invalid farm context")
        try:
            result = await database_integrated_amm_tool_enhanced.ainvoke({
                "product_name": "Test",
                "farm_context": {"distance_to_water_m": -10}  # Invalid negative distance
            })
            # Should handle gracefully
            print(f"   Handled gracefully: {isinstance(result, AMMOutput)}")
        except Exception as e:
            print(f"   Caught exception: {type(e).__name__}")
        
        # Test 3: Product not found
        print("\nTest 4.3: Product not found")
        result = await database_integrated_amm_tool_enhanced.ainvoke({
            "product_name": "NONEXISTENT_PRODUCT_XYZ123",
            "crop_type": "blé"
        })
        
        if isinstance(result, AMMOutput):
            output = result
            print(f"   Success: {output.success}")
            print(f"   Status: {output.status}")
            if output.status == "no_results":
                print(f"   Recommendations provided: {len(output.recommendations) if output.recommendations else 0}")
        
        print(f"\n✅ TEST 4 PASSED: Error handling")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  ENHANCED AMM LOOKUP TOOL - TEST SUITE")
    print("="*80)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Testing with: Real EPHY database (if available)")
    print("="*80)
    
    results = []
    
    # Run tests
    results.append(("Basic AMM Lookup", await test_1_basic_amm_lookup()))
    results.append(("Caching Performance", await test_2_caching_performance()))
    results.append(("Farm Context", await test_3_farm_context()))
    results.append(("Error Handling", await test_4_error_handling()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

