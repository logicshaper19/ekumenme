"""
Test Enhanced Diagnose Disease Tool

Tests the enhanced disease diagnosis tool with:
- Database integration
- BBCH stage integration
- Pydantic schemas
- Redis caching
- Error handling
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.crop_health_agent.diagnose_disease_tool_enhanced import (
    diagnose_disease_tool_enhanced
)


async def test_basic_disease_diagnosis():
    """Test 1: Basic disease diagnosis with symptoms"""
    print("\n" + "="*80)
    print("TEST 1: Basic Disease Diagnosis - Wheat Yellow Rust")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "pustules_jaunes", "feuilles_jaunies"]
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    print(f"🎯 Confidence: {data['diagnosis_confidence']}")
    print(f"📚 Data Source: {data['data_source']}")
    
    if data['diagnoses']:
        print(f"\n🔍 Top Diagnosis:")
        top = data['diagnoses'][0]
        print(f"   Disease: {top['disease_name']}")
        print(f"   Scientific Name: {top.get('scientific_name', 'N/A')}")
        print(f"   Type: {top['disease_type']}")
        print(f"   Confidence: {top['confidence']:.2%}")
        print(f"   Severity: {top['severity']}")
        print(f"   Matched Symptoms: {', '.join(top['symptoms_matched'][:3])}")
        print(f"   Treatments: {', '.join(top['treatment_recommendations'][:3])}")
    
    assert data['success'], "Diagnosis should succeed"
    assert data['total_diagnoses'] > 0, "Should have at least one diagnosis"
    print("\n✅ TEST 1 PASSED")


async def test_disease_with_environmental_conditions():
    """Test 2: Disease diagnosis with environmental conditions"""
    print("\n" + "="*80)
    print("TEST 2: Disease Diagnosis with Environmental Conditions")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_brunes", "nécroses_feuilles", "pycnides_noires"],
        "environmental_conditions": {
            "temperature_c": 15.0,
            "humidity_percent": 85.0,
            "rainfall_mm": 25.0,
            "soil_moisture": "wet"
        }
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    print(f"🎯 Confidence: {data['diagnosis_confidence']}")
    
    if data['environmental_conditions']:
        print(f"\n🌡️ Environmental Conditions:")
        env = data['environmental_conditions']
        print(f"   Temperature: {env.get('temperature_c')}°C")
        print(f"   Humidity: {env.get('humidity_percent')}%")
        print(f"   Rainfall: {env.get('rainfall_mm')}mm")
        print(f"   Soil Moisture: {env.get('soil_moisture')}")
    
    if data['diagnoses']:
        print(f"\n🔍 Top Diagnosis:")
        top = data['diagnoses'][0]
        print(f"   Disease: {top['disease_name']}")
        print(f"   Confidence: {top['confidence']:.2%}")
        print(f"   Severity: {top['severity']}")
    
    assert data['success'], "Diagnosis should succeed"
    print("\n✅ TEST 2 PASSED")


async def test_disease_with_bbch_stage():
    """Test 3: Disease diagnosis with BBCH growth stage"""
    print("\n" + "="*80)
    print("TEST 3: Disease Diagnosis with BBCH Growth Stage")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "pustules_jaunes"],
        "bbch_stage": 31,  # Stem elongation
        "environmental_conditions": {
            "temperature_c": 18.0,
            "humidity_percent": 75.0
        }
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    
    if data['bbch_stage'] is not None:
        print(f"\n🌱 BBCH Stage: {data['bbch_stage']}")
        if data['bbch_stage_description']:
            print(f"   Description: {data['bbch_stage_description']}")
    
    if data['diagnoses']:
        print(f"\n🔍 Top Diagnosis:")
        top = data['diagnoses'][0]
        print(f"   Disease: {top['disease_name']}")
        print(f"   Confidence: {top['confidence']:.2%}")
        if top.get('susceptible_bbch_stages'):
            print(f"   Susceptible BBCH Stages: {top['susceptible_bbch_stages']}")
    
    assert data['success'], "Diagnosis should succeed"
    print("\n✅ TEST 3 PASSED")


async def test_corn_disease():
    """Test 4: Corn disease diagnosis"""
    print("\n" + "="*80)
    print("TEST 4: Corn Disease Diagnosis - Helminthosporiose")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "maïs",
        "symptoms": ["taches_allongées", "nécroses_feuilles", "lésions_brunes"],
        "environmental_conditions": {
            "temperature_c": 25.0,
            "humidity_percent": 80.0
        }
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    print(f"🎯 Confidence: {data['diagnosis_confidence']}")
    
    if data['diagnoses']:
        print(f"\n🔍 Top Diagnosis:")
        top = data['diagnoses'][0]
        print(f"   Disease: {top['disease_name']}")
        print(f"   Scientific Name: {top.get('scientific_name', 'N/A')}")
        print(f"   Confidence: {top['confidence']:.2%}")
        print(f"   Severity: {top['severity']}")
    
    assert data['success'], "Diagnosis should succeed"
    assert data['total_diagnoses'] > 0, "Should have at least one diagnosis"
    print("\n✅ TEST 4 PASSED")


async def test_rapeseed_disease():
    """Test 5: Rapeseed disease diagnosis"""
    print("\n" + "="*80)
    print("TEST 5: Rapeseed Disease Diagnosis - Phoma")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "colza",
        "symptoms": ["taches_circulaires", "nécroses_collet", "chancres_tiges"],
        "environmental_conditions": {
            "temperature_c": 12.0,
            "humidity_percent": 85.0
        },
        "affected_area_percent": 35.0
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    print(f"🎯 Confidence: {data['diagnosis_confidence']}")
    
    if data['diagnoses']:
        print(f"\n🔍 Top Diagnosis:")
        top = data['diagnoses'][0]
        print(f"   Disease: {top['disease_name']}")
        print(f"   Scientific Name: {top.get('scientific_name', 'N/A')}")
        print(f"   Confidence: {top['confidence']:.2%}")
        print(f"   Severity: {top['severity']}")
        print(f"   Prevention: {', '.join(top['prevention_measures'][:3])}")
    
    assert data['success'], "Diagnosis should succeed"
    assert data['total_diagnoses'] > 0, "Should have at least one diagnosis"
    print("\n✅ TEST 5 PASSED")


async def test_unknown_crop():
    """Test 6: Unknown crop handling"""
    print("\n" + "="*80)
    print("TEST 6: Unknown Crop Handling")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "unknown_crop_xyz",
        "symptoms": ["taches_jaunes", "feuilles_jaunies"]
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    print(f"📚 Data Source: {data['data_source']}")
    
    # Should still succeed but with no diagnoses or low confidence
    assert data['success'], "Should handle unknown crop gracefully"
    print("\n✅ TEST 6 PASSED")


async def test_consolidated_treatments():
    """Test 7: Consolidated treatment recommendations"""
    print("\n" + "="*80)
    print("TEST 7: Consolidated Treatment Recommendations")
    print("="*80)
    
    result = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "taches_brunes", "pustules_jaunes", "nécroses_feuilles"],
        "environmental_conditions": {
            "temperature_c": 16.0,
            "humidity_percent": 80.0,
            "rainfall_mm": 20.0
        }
    })
    
    data = json.loads(result)
    print(f"\n✅ Success: {data['success']}")
    print(f"📊 Total Diagnoses: {data['total_diagnoses']}")
    
    if data['treatment_recommendations']:
        print(f"\n💊 Consolidated Treatment Recommendations:")
        for i, treatment in enumerate(data['treatment_recommendations'][:5], 1):
            print(f"   {i}. {treatment}")
    
    assert data['success'], "Diagnosis should succeed"
    assert len(data['treatment_recommendations']) > 0, "Should have treatment recommendations"
    print("\n✅ TEST 7 PASSED")


async def test_caching_performance():
    """Test 8: Caching performance"""
    print("\n" + "="*80)
    print("TEST 8: Caching Performance")
    print("="*80)
    
    import time
    
    # First call (cache miss)
    start = time.time()
    result1 = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "pustules_jaunes"]
    })
    time1 = time.time() - start
    
    # Second call (cache hit)
    start = time.time()
    result2 = await diagnose_disease_tool_enhanced.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "pustules_jaunes"]
    })
    time2 = time.time() - start
    
    print(f"\n⏱️ First call (cache miss): {time1:.3f}s")
    print(f"⏱️ Second call (cache hit): {time2:.3f}s")
    print(f"🚀 Speedup: {time1/time2:.1f}x faster")
    
    data1 = json.loads(result1)
    data2 = json.loads(result2)
    
    assert data1['success'] and data2['success'], "Both calls should succeed"
    assert data1['total_diagnoses'] == data2['total_diagnoses'], "Results should be identical"
    print("\n✅ TEST 8 PASSED")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING ENHANCED DISEASE DIAGNOSIS TOOL")
    print("="*80)
    
    tests = [
        test_basic_disease_diagnosis,
        test_disease_with_environmental_conditions,
        test_disease_with_bbch_stage,
        test_corn_disease,
        test_rapeseed_disease,
        test_unknown_crop,
        test_consolidated_treatments,
        test_caching_performance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print(f"📈 Success Rate: {passed/len(tests)*100:.1f}%")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

