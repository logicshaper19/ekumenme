#!/usr/bin/env python3
"""
Test Improved Disease Diagnosis Tool

Tests the enhanced features:
1. Fuzzy symptom matching
2. BBCH stage integration in confidence calculation
3. Proper environmental condition matching
4. Input validation
5. Real database integration with 16 diseases
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "Ekumen-assistant"))

import asyncio
import json
from datetime import datetime

from app.tools.crop_health_agent.diagnose_disease_tool_enhanced import diagnose_disease_tool_enhanced as diagnose_disease_tool


async def test_fuzzy_symptom_matching():
    """Test fuzzy symptom matching (typos, variations)"""
    print("\n" + "="*80)
    print("TEST 1: Fuzzy Symptom Matching - Typos and Variations")
    print("="*80)
    
    # Test with slight typos and variations
    result_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["tache jaune", "pustule jaune", "feuille jaunie"],  # Singular instead of plural
        "environmental_conditions": {
            "temperature_c": 15,
            "humidity_percent": 80
        }
    })
    
    result = json.loads(result_json)
    
    print(f"✅ Success: {result['success']}")
    print(f"📊 Total Diagnoses: {result['total_diagnoses']}")
    print(f"📚 Data Source: {result['data_source']}")
    
    if result['diagnoses']:
        top = result['diagnoses'][0]
        print(f"\n🔍 Top Diagnosis:")
        print(f"   Disease: {top['disease_name']}")
        print(f"   Confidence: {top['confidence']*100:.2f}%")
        print(f"   Matched Symptoms: {', '.join(top['symptoms_matched'])}")
    
    assert result['success'], "Diagnosis should succeed"
    assert result['total_diagnoses'] > 0, "Should find diseases with fuzzy matching"
    print("\n✅ TEST 1 PASSED - Fuzzy matching works!")


async def test_bbch_stage_confidence_boost():
    """Test BBCH stage integration - confidence boost at susceptible stage"""
    print("\n" + "="*80)
    print("TEST 2: BBCH Stage Confidence Boost")
    print("="*80)
    
    # Test 1: Wheat yellow rust at susceptible stage (BBCH 31 - stem elongation)
    result1_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "pustules_jaunes"],
        "bbch_stage": 31,  # Susceptible stage for yellow rust
        "environmental_conditions": {
            "temperature_c": 15,
            "humidity_percent": 85
        }
    })
    
    result1 = json.loads(result1_json)
    
    # Test 2: Same symptoms but at non-susceptible stage (BBCH 85 - ripening)
    result2_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes", "pustules_jaunes"],
        "bbch_stage": 85,  # Non-susceptible stage
        "environmental_conditions": {
            "temperature_c": 15,
            "humidity_percent": 85
        }
    })
    
    result2 = json.loads(result2_json)
    
    print(f"\n📊 At Susceptible Stage (BBCH 31):")
    if result1['diagnoses']:
        print(f"   Confidence: {result1['diagnoses'][0]['confidence']*100:.2f}%")
    
    print(f"\n📊 At Non-Susceptible Stage (BBCH 85):")
    if result2['diagnoses']:
        print(f"   Confidence: {result2['diagnoses'][0]['confidence']*100:.2f}%")
    
    # Confidence should be higher at susceptible stage
    if result1['diagnoses'] and result2['diagnoses']:
        conf1 = result1['diagnoses'][0]['confidence']
        conf2 = result2['diagnoses'][0]['confidence']
        print(f"\n🎯 Confidence Boost: {((conf1/conf2 - 1) * 100):.1f}% higher at susceptible stage")
        assert conf1 > conf2, "Confidence should be higher at susceptible BBCH stage"
    
    print("\n✅ TEST 2 PASSED - BBCH stage affects confidence!")


async def test_environmental_condition_matching():
    """Test proper environmental condition matching"""
    print("\n" + "="*80)
    print("TEST 3: Environmental Condition Matching")
    print("="*80)
    
    # Test 1: Perfect conditions for septoriose (high humidity, moderate temp, rainfall)
    result1_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_brunes", "nécroses_feuilles"],
        "environmental_conditions": {
            "temperature_c": 18,  # Moderate (15-25°C range)
            "humidity_percent": 85,  # High
            "rainfall_mm": 10  # Frequent
        }
    })
    
    result1 = json.loads(result1_json)
    
    # Test 2: Poor conditions for septoriose (low humidity, hot, no rain)
    result2_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_brunes", "nécroses_feuilles"],
        "environmental_conditions": {
            "temperature_c": 30,  # Too hot
            "humidity_percent": 30,  # Low
            "rainfall_mm": 0  # No rain
        }
    })
    
    result2 = json.loads(result2_json)
    
    print(f"\n📊 With Favorable Conditions:")
    if result1['diagnoses']:
        print(f"   Confidence: {result1['diagnoses'][0]['confidence']*100:.2f}%")
    
    print(f"\n📊 With Unfavorable Conditions:")
    if result2['diagnoses']:
        print(f"   Confidence: {result2['diagnoses'][0]['confidence']*100:.2f}%")
    
    # Confidence should be higher with favorable conditions
    if result1['diagnoses'] and result2['diagnoses']:
        conf1 = result1['diagnoses'][0]['confidence']
        conf2 = result2['diagnoses'][0]['confidence']
        print(f"\n🎯 Confidence Difference: {((conf1/conf2 - 1) * 100):.1f}% higher with favorable conditions")
        assert conf1 > conf2, "Confidence should be higher with favorable environmental conditions"
    
    print("\n✅ TEST 3 PASSED - Environmental conditions affect confidence!")


async def test_input_validation():
    """Test input validation"""
    print("\n" + "="*80)
    print("TEST 4: Input Validation")
    print("="*80)
    
    # Test 1: Invalid BBCH stage (> 99)
    result1_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes"],
        "bbch_stage": 150  # Invalid
    })
    
    result1 = json.loads(result1_json)
    
    print(f"\n📊 Invalid BBCH Stage (150):")
    print(f"   Success: {result1['success']}")
    print(f"   Error: {result1.get('error', 'None')}")
    print(f"   Error Type: {result1.get('error_type', 'None')}")
    
    assert not result1['success'], "Should fail with invalid BBCH stage"
    assert result1['error_type'] == "validation", "Should be validation error"
    
    # Test 2: Invalid affected area (> 100%)
    result2_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["taches_jaunes"],
        "affected_area_percent": 150  # Invalid
    })
    
    result2 = json.loads(result2_json)
    
    print(f"\n📊 Invalid Affected Area (150%):")
    print(f"   Success: {result2['success']}")
    print(f"   Error: {result2.get('error', 'None')}")
    
    assert not result2['success'], "Should fail with invalid affected area"
    
    # Test 3: No symptoms
    result3_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": []  # Empty
    })
    
    result3 = json.loads(result3_json)
    
    print(f"\n📊 No Symptoms:")
    print(f"   Success: {result3['success']}")
    print(f"   Error: {result3.get('error', 'None')}")
    
    assert not result3['success'], "Should fail with no symptoms"
    
    print("\n✅ TEST 4 PASSED - Input validation works!")


async def test_database_integration():
    """Test real database integration with 16 diseases"""
    print("\n" + "="*80)
    print("TEST 5: Real Database Integration (16 Diseases)")
    print("="*80)
    
    # Test wheat disease from database
    result_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": ["pustules_brunes", "taches_brunes", "feuilles_brunies"],
        "environmental_conditions": {
            "temperature_c": 20,
            "humidity_percent": 80
        },
        "bbch_stage": 55  # Heading stage
    })
    
    result = json.loads(result_json)
    
    print(f"✅ Success: {result['success']}")
    print(f"📊 Total Diagnoses: {result['total_diagnoses']}")
    print(f"📚 Data Source: {result['data_source']}")
    print(f"🎯 Confidence: {result['diagnosis_confidence']}")
    
    if result['diagnoses']:
        for i, diag in enumerate(result['diagnoses'][:3], 1):
            print(f"\n🔍 Diagnosis {i}:")
            print(f"   Disease: {diag['disease_name']}")
            print(f"   Scientific: {diag.get('scientific_name', 'N/A')}")
            print(f"   Confidence: {diag['confidence']*100:.2f}%")
            print(f"   Severity: {diag['severity']}")
            if diag.get('eppo_code'):
                print(f"   EPPO Code: {diag['eppo_code']}")
    
    assert result['success'], "Diagnosis should succeed"
    assert result['data_source'] in ["database", "hybrid"], "Should use database"
    print("\n✅ TEST 5 PASSED - Database integration works!")


async def test_comprehensive_scenario():
    """Test comprehensive real-world scenario"""
    print("\n" + "="*80)
    print("TEST 6: Comprehensive Real-World Scenario")
    print("="*80)
    
    # Farmer observes yellow rust on wheat at stem elongation stage
    result_json = await diagnose_disease_tool.ainvoke({
        "crop_type": "blé",
        "symptoms": [
            "taches_jaunes",
            "pustules_jaunes",
            "stries_jaunes",
            "feuilles_jaunies"
        ],
        "environmental_conditions": {
            "temperature_c": 12,  # Cool-moderate (10-20°C optimal for yellow rust)
            "humidity_percent": 90,  # High humidity
            "rainfall_mm": 5
        },
        "bbch_stage": 31,  # Stem elongation - highly susceptible
        "affected_area_percent": 15.5,
        "field_location": "Parcelle Nord"
    })
    
    result = json.loads(result_json)
    
    print(f"✅ Success: {result['success']}")
    print(f"📊 Total Diagnoses: {result['total_diagnoses']}")
    print(f"📚 Data Source: {result['data_source']}")
    print(f"🎯 Overall Confidence: {result['diagnosis_confidence']}")
    print(f"🌱 BBCH Stage: {result.get('bbch_stage')} - {result.get('bbch_stage_description', 'N/A')}")
    
    if result['diagnoses']:
        top = result['diagnoses'][0]
        print(f"\n🔍 Top Diagnosis:")
        print(f"   Disease: {top['disease_name']}")
        print(f"   Scientific: {top.get('scientific_name', 'N/A')}")
        print(f"   Confidence: {top['confidence']*100:.2f}%")
        print(f"   Severity: {top['severity']}")
        print(f"   Type: {top['disease_type']}")
        
        if top.get('eppo_code'):
            print(f"   EPPO Code: {top['eppo_code']}")
        
        print(f"\n💊 Treatment Recommendations:")
        for treatment in top.get('treatment_recommendations', [])[:3]:
            print(f"   - {treatment}")
        
        print(f"\n🛡️ Prevention Measures:")
        for prevention in top.get('prevention_measures', [])[:3]:
            print(f"   - {prevention}")
    
    print(f"\n💊 Consolidated Treatments:")
    for treatment in result.get('treatment_recommendations', [])[:5]:
        print(f"   - {treatment}")
    
    assert result['success'], "Diagnosis should succeed"
    assert result['total_diagnoses'] > 0, "Should find diseases"
    print("\n✅ TEST 6 PASSED - Comprehensive scenario works!")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING IMPROVED DISEASE DIAGNOSIS TOOL")
    print("="*80)
    print("Testing enhanced features:")
    print("  1. Fuzzy symptom matching")
    print("  2. BBCH stage confidence adjustment")
    print("  3. Environmental condition matching")
    print("  4. Input validation")
    print("  5. Real database integration (16 diseases)")
    print("  6. Comprehensive real-world scenario")
    print("="*80)
    
    tests = [
        ("Fuzzy Symptom Matching", test_fuzzy_symptom_matching),
        ("BBCH Stage Confidence Boost", test_bbch_stage_confidence_boost),
        ("Environmental Condition Matching", test_environmental_condition_matching),
        ("Input Validation", test_input_validation),
        ("Database Integration", test_database_integration),
        ("Comprehensive Scenario", test_comprehensive_scenario),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print(f"📈 Success Rate: {(passed/len(tests)*100):.1f}%")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

