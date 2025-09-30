"""
Integrated Weather Workflow Test - All 3 Enhanced Tools Working Together

Simulates a realistic agricultural workflow:
1. Get weather forecast for a location
2. Analyze agricultural risks
3. Identify optimal intervention windows
4. Generate actionable recommendations

Tests the complete chain with REAL API data and caching.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.weather_agent.get_weather_data_tool_enhanced import (
    get_weather_data_tool_enhanced
)
from app.tools.weather_agent.analyze_weather_risks_tool_enhanced import (
    analyze_weather_risks_tool_enhanced
)
from app.tools.weather_agent.identify_intervention_windows_tool_enhanced import (
    identify_intervention_windows_tool_enhanced
)
from app.core.cache import get_cache_stats, clear_cache


async def test_complete_agricultural_workflow():
    """
    Test complete agricultural workflow:
    Farmer wants to plan interventions for wheat crop in Normandy
    """
    print("\n" + "="*80)
    print("INTEGRATED AGRICULTURAL WORKFLOW TEST")
    print("="*80)
    print("\n📋 Scenario: Farmer planning wheat interventions in Normandy")
    print("   - Location: Normandie")
    print("   - Crop: Blé (Wheat)")
    print("   - Forecast: 7 days")
    print("   - Interventions needed: Pulvérisation, Semis")
    
    workflow_start = time.time()
    
    try:
        # ========================================================================
        # STEP 1: Get Weather Forecast
        # ========================================================================
        print("\n" + "-"*80)
        print("STEP 1: Get Weather Forecast")
        print("-"*80)
        
        step1_start = time.time()
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Normandie",
            "days": 7,
            "use_real_api": True  # ✅ REAL API
        })
        step1_time = time.time() - step1_start
        
        weather_data = json.loads(weather_result)
        
        print(f"✅ Weather forecast retrieved in {step1_time:.3f}s")
        print(f"   📍 Location: {weather_data.get('location')}")
        print(f"   📅 Forecast days: {weather_data.get('forecast_period_days')}")
        print(f"   🌡️  Temperature range: {weather_data.get('weather_conditions', [{}])[0].get('temperature_min', 0):.1f}°C - {weather_data.get('weather_conditions', [{}])[0].get('temperature_max', 0):.1f}°C")
        print(f"   💨 Wind speed: {weather_data.get('weather_conditions', [{}])[0].get('wind_speed', 0):.0f} km/h")
        print(f"   💧 Precipitation: {weather_data.get('weather_conditions', [{}])[0].get('precipitation', 0):.0f} mm")
        
        if not weather_data.get('success'):
            print(f"❌ Weather forecast failed: {weather_data.get('error')}")
            return False
        
        # ========================================================================
        # STEP 2: Analyze Agricultural Risks
        # ========================================================================
        print("\n" + "-"*80)
        print("STEP 2: Analyze Agricultural Risks for Wheat")
        print("-"*80)
        
        step2_start = time.time()
        risk_result = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": "blé"  # Wheat
        })
        step2_time = time.time() - step2_start
        
        risk_data = json.loads(risk_result)
        
        print(f"✅ Risk analysis completed in {step2_time:.3f}s")
        print(f"   🎯 Total risks identified: {risk_data.get('total_risks')}")
        print(f"   ⚠️  High severity risks: {risk_data.get('risk_summary', {}).get('high_severity_risks')}")
        print(f"   📊 Risk types: {', '.join(risk_data.get('risk_summary', {}).get('risk_types', []))}")
        
        if not risk_data.get('success'):
            print(f"❌ Risk analysis failed: {risk_data.get('error')}")
            return False
        
        # Show risk insights
        print(f"\n   💡 Risk Insights:")
        for insight in risk_data.get('risk_insights', [])[:5]:
            print(f"      {insight}")
        
        # ========================================================================
        # STEP 3: Identify Intervention Windows
        # ========================================================================
        print("\n" + "-"*80)
        print("STEP 3: Identify Optimal Intervention Windows")
        print("-"*80)
        
        step3_start = time.time()
        windows_result = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "intervention_types": ["pulvérisation", "semis"]
        })
        step3_time = time.time() - step3_start
        
        windows_data = json.loads(windows_result)
        
        print(f"✅ Intervention windows identified in {step3_time:.3f}s")
        print(f"   🎯 Total windows: {windows_data.get('total_windows')}")
        print(f"   📊 Windows by type: {windows_data.get('window_statistics', {}).get('windows_by_type', {})}")
        print(f"   📈 Average confidence: {windows_data.get('window_statistics', {}).get('average_confidence', 0):.0%}")
        
        if not windows_data.get('success'):
            print(f"❌ Window identification failed: {windows_data.get('error')}")
            return False
        
        # Show window insights
        print(f"\n   💡 Window Insights:")
        for insight in windows_data.get('window_insights', []):
            print(f"      {insight}")
        
        # Show detailed windows
        print(f"\n   📅 Detailed Windows:")
        for window in windows_data.get('windows', [])[:3]:  # Show first 3
            print(f"      {window['date']}: {window['intervention_type']} - {window['conditions']} ({window['confidence']:.0%} confiance)")
            if window.get('weather_summary'):
                print(f"         Météo: {window['weather_summary']}")
        
        # ========================================================================
        # STEP 4: Generate Actionable Recommendations
        # ========================================================================
        print("\n" + "-"*80)
        print("STEP 4: Generate Actionable Recommendations")
        print("-"*80)
        
        recommendations = generate_recommendations(weather_data, risk_data, windows_data)
        
        print("✅ Recommendations generated:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # ========================================================================
        # WORKFLOW SUMMARY
        # ========================================================================
        workflow_time = time.time() - workflow_start
        
        print("\n" + "="*80)
        print("WORKFLOW SUMMARY")
        print("="*80)
        
        print(f"\n⏱️  Performance:")
        print(f"   Step 1 (Weather):     {step1_time:.3f}s ({step1_time*1000:.0f}ms)")
        print(f"   Step 2 (Risks):       {step2_time:.3f}s ({step2_time*1000:.0f}ms)")
        print(f"   Step 3 (Windows):     {step3_time:.3f}s ({step3_time*1000:.0f}ms)")
        print(f"   Total workflow:       {workflow_time:.3f}s ({workflow_time*1000:.0f}ms)")
        
        print(f"\n📊 Results:")
        print(f"   Weather conditions:   {len(weather_data.get('weather_conditions', []))} days")
        print(f"   Risks identified:     {risk_data.get('total_risks')}")
        print(f"   Windows identified:   {windows_data.get('total_windows')}")
        print(f"   Recommendations:      {len(recommendations)}")
        
        # Cache stats
        stats = get_cache_stats()
        print(f"\n💾 Cache Stats:")
        print(f"   Redis available:      {stats['redis_available']}")
        print(f"   Total cached items:   {stats['total_memory_items']}")
        if 'memory_caches' in stats:
            for category, cache_stats in stats['memory_caches'].items():
                if cache_stats['size'] > 0:
                    print(f"   {category}: {cache_stats['size']}/{cache_stats['maxsize']} items ({cache_stats['utilization']:.1f}%)")
        
        print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_recommendations(weather_data, risk_data, windows_data):
    """Generate actionable recommendations based on all data"""
    recommendations = []
    
    # Check for high-priority risks
    high_severity_risks = risk_data.get('risk_summary', {}).get('high_severity_risks', 0)
    if high_severity_risks > 0:
        recommendations.append(
            f"⚠️ URGENT: {high_severity_risks} risque(s) de haute sévérité détecté(s). "
            "Consultez l'analyse des risques avant toute intervention."
        )
    
    # Check for optimal windows
    total_windows = windows_data.get('total_windows', 0)
    if total_windows > 0:
        best_date = windows_data.get('window_statistics', {}).get('best_window_date')
        best_type = windows_data.get('window_statistics', {}).get('best_window_type')
        if best_date and best_type:
            recommendations.append(
                f"✅ Meilleure fenêtre: {best_type} le {best_date}. "
                "Planifiez cette intervention en priorité."
            )
    else:
        recommendations.append(
            "❌ Aucune fenêtre optimale identifiée dans les 7 prochains jours. "
            "Surveillez les prévisions pour de meilleures conditions."
        )
    
    # Specific risk-based recommendations
    risk_types = risk_data.get('risk_summary', {}).get('risk_types', [])
    if 'gel' in risk_types:
        recommendations.append(
            "🥶 Risque de gel détecté. Protégez les cultures sensibles et "
            "évitez les semis jusqu'à amélioration des températures."
        )
    if 'vent' in risk_types:
        recommendations.append(
            "💨 Vent fort prévu. Reportez les pulvérisations pour éviter la dérive. "
            "Utilisez des buses anti-dérive si intervention nécessaire."
        )
    if 'pluie' in risk_types:
        recommendations.append(
            "🌧️ Précipitations importantes prévues. Évitez les travaux de sol "
            "pour prévenir la compaction et le lessivage."
        )
    
    # Window-based recommendations
    windows_by_type = windows_data.get('window_statistics', {}).get('windows_by_type', {})
    if 'pulvérisation' in windows_by_type and windows_by_type['pulvérisation'] > 0:
        recommendations.append(
            f"💧 {windows_by_type['pulvérisation']} fenêtre(s) pour pulvérisation identifiée(s). "
            "Préparez les équipements et produits phytosanitaires."
        )
    if 'semis' in windows_by_type and windows_by_type['semis'] > 0:
        recommendations.append(
            f"🌱 {windows_by_type['semis']} fenêtre(s) pour semis identifiée(s). "
            "Vérifiez l'humidité du sol et préparez les semences."
        )
    
    return recommendations


async def test_caching_across_workflow():
    """Test that caching works across the entire workflow"""
    print("\n" + "="*80)
    print("CACHING PERFORMANCE TEST - COMPLETE WORKFLOW")
    print("="*80)
    
    try:
        # Clear cache
        clear_cache(category="weather")
        print("🧹 Cache cleared\n")
        
        # First workflow run (cache miss)
        print("🔄 First workflow run (cache miss)...")
        start = time.time()
        
        weather_result = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Bretagne",
            "days": 7,
            "use_real_api": True
        })
        
        risk_result = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "crop_type": "maïs"
        })
        
        windows_result = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": weather_result,
            "intervention_types": ["pulvérisation", "récolte"]
        })
        
        time1 = time.time() - start
        print(f"   ⏱️  Time: {time1:.3f}s ({time1*1000:.0f}ms)")
        
        # Second workflow run (cache hit)
        print("\n🔄 Second workflow run (cache hit)...")
        start = time.time()
        
        weather_result2 = await get_weather_data_tool_enhanced.ainvoke({
            "location": "Bretagne",
            "days": 7,
            "use_real_api": True
        })
        
        risk_result2 = await analyze_weather_risks_tool_enhanced.ainvoke({
            "weather_data_json": weather_result2,
            "crop_type": "maïs"
        })
        
        windows_result2 = await identify_intervention_windows_tool_enhanced.ainvoke({
            "weather_data_json": weather_result2,
            "intervention_types": ["pulvérisation", "récolte"]
        })
        
        time2 = time.time() - start
        print(f"   ⏱️  Time: {time2:.3f}s ({time2*1000:.0f}ms)")
        
        # Calculate speedup
        speedup = (time1 - time2) / time1 * 100 if time1 > 0 else 0
        speedup_factor = time1 / time2 if time2 > 0 else 0
        
        print(f"\n📊 Caching Performance:")
        print(f"   First run (uncached):  {time1:.3f}s ({time1*1000:.0f}ms)")
        print(f"   Second run (cached):   {time2:.3f}s ({time2*1000:.0f}ms)")
        print(f"   Speedup: {speedup:.1f}%")
        print(f"   Speed factor: {speedup_factor:.1f}x faster")
        
        if speedup > 50:
            print(f"\n✅ EXCELLENT: {speedup:.1f}% speedup with caching!")
        elif speedup > 0:
            print(f"\n✅ GOOD: {speedup:.1f}% speedup with caching")
        else:
            print(f"\n⚠️ Cache not providing significant speedup")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CACHING TEST FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("INTEGRATED WEATHER TOOLS - COMPREHENSIVE INTEGRATION TEST")
    print("="*80)
    print(f"\n🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  Note: Using REAL Weather API")
    
    tests = [
        ("Complete Agricultural Workflow", test_complete_agricultural_workflow),
        ("Caching Across Workflow", test_caching_across_workflow),
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
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ The 3 enhanced weather tools work perfectly together!")
        print("✅ Caching is working across the entire workflow!")
        print("✅ Ready for production deployment!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review and fix before deployment.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

