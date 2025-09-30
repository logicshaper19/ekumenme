#!/usr/bin/env python3
"""
Test DiagnoseDiseaseTool with newly added crops
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import json
from app.tools.crop_health_agent.diagnose_disease_tool_enhanced import DiagnoseDiseaseService
from app.tools.schemas.disease_schemas import EnvironmentalConditions


async def test_potato_late_blight():
    """Test diagnosis of potato late blight (Mildiou)"""
    print("\n" + "="*80)
    print("TEST 1: Potato Late Blight (Mildiou) - Critical Disease")
    print("="*80)

    service = DiagnoseDiseaseService()

    # Simulate classic late blight symptoms
    result = await service.diagnose_disease(
        crop_type="pomme_de_terre",
        symptoms=[
            "taches_brunes_humides",
            "lésions_aqueuses",
            "pourriture_tubercules",
            "feuilles_nécrosées"
        ],
        environmental_conditions=EnvironmentalConditions(
            temperature_c=18.0,
            humidity_percent=85.0,
            rainfall_mm=15.0
        ),
        bbch_stage=55,  # Flowering stage - highly susceptible
        field_location="Bretagne",
        affected_area_percent=35.0
    )

    print("\n📋 Input:")
    print(f"  Crop: Pomme de terre (Potato)")
    print(f"  Symptoms: taches_brunes_humides, lésions_aqueuses, pourriture_tubercules")
    print(f"  BBCH Stage: 55 (Flowering - highly susceptible)")
    print(f"  Conditions: High humidity, moderate temp, frequent rain")
    print(f"  Affected Area: 35%")

    result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
    print("\n🔍 Diagnosis Result:")
    print(f"  Success: {result_dict['success']}")
    
    if result_dict['success'] and result_dict.get('diagnoses'):
        for i, diagnosis in enumerate(result_dict['diagnoses'][:3], 1):
            print(f"\n  {i}. {diagnosis.get('disease_name', 'Unknown')} ({diagnosis.get('scientific_name', 'N/A')})")
            if 'confidence_score' in diagnosis:
                print(f"     Confidence: {diagnosis['confidence_score']:.1%}")
            print(f"     Severity: {diagnosis.get('severity_level', 'N/A')}")
            if 'matched_symptoms' in diagnosis:
                print(f"     Matched Symptoms: {len(diagnosis['matched_symptoms'])}")
            if diagnosis.get('treatment_recommendations'):
                print(f"     Treatments: {', '.join(diagnosis['treatment_recommendations'][:2])}")
    else:
        print(f"  Error: {result_dict.get('error', 'Unknown error')}")
    
    # Verify Mildiou is top result
    if result_dict['success'] and result_dict.get('diagnoses'):
        top_disease = result_dict['diagnoses'][0]['disease_name']
        if top_disease == "Mildiou":
            print("\n✅ TEST PASSED: Mildiou correctly identified as top diagnosis")
            return True
        else:
            print(f"\n❌ TEST FAILED: Expected 'Mildiou', got '{top_disease}'")
            return False
    else:
        print("\n❌ TEST FAILED: No diagnoses returned")
        return False


async def test_grapevine_downy_mildew():
    """Test diagnosis of grapevine downy mildew"""
    print("\n" + "="*80)
    print("TEST 2: Grapevine Downy Mildew (Mildiou de la vigne)")
    print("="*80)

    service = DiagnoseDiseaseService()

    result = await service.diagnose_disease(
        crop_type="vigne",
        symptoms=[
            "taches_huile",
            "duvet_blanc",
            "taches_jaunes_dessus",
            "baies_flétries"
        ],
        environmental_conditions=EnvironmentalConditions(
            temperature_c=20.0,
            humidity_percent=90.0,
            rainfall_mm=12.0
        ),
        bbch_stage=65,  # Flowering - highly susceptible
        field_location="Bordeaux",
        affected_area_percent=25.0
    )

    print("\n📋 Input:")
    print(f"  Crop: Vigne (Grapevine)")
    print(f"  Symptoms: taches_huile, duvet_blanc, taches_jaunes_dessus")
    print(f"  BBCH Stage: 65 (Flowering)")
    print(f"  Conditions: High humidity, moderate temp, frequent rain")
    print(f"  Affected Area: 25%")

    result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
    print("\n🔍 Diagnosis Result:")
    print(f"  Success: {result_dict['success']}")
    
    if result_dict['success'] and result_dict.get('diagnoses'):
        for i, diagnosis in enumerate(result_dict['diagnoses'][:3], 1):
            print(f"\n  {i}. {diagnosis['disease_name']} ({diagnosis.get('scientific_name', 'N/A')})")
            print(f"     Confidence: {diagnosis['confidence_score']:.1%}")
            print(f"     Severity: {diagnosis['severity_level']}")
            print(f"     Matched Symptoms: {len(diagnosis.get('matched_symptoms', []))}")
    else:
        print(f"  Error: {result_dict.get('error', 'Unknown error')}")
    
    # Verify Mildiou de la vigne is in top results
    if result_dict['success'] and result_dict.get('diagnoses'):
        disease_names = [d['disease_name'] for d in result_dict['diagnoses'][:3]]
        if "Mildiou de la vigne" in disease_names:
            print("\n✅ TEST PASSED: Mildiou de la vigne in top 3 diagnoses")
            return True
        else:
            print(f"\n❌ TEST FAILED: Mildiou de la vigne not in top 3: {disease_names}")
            return False
    else:
        print("\n❌ TEST FAILED: No diagnoses returned")
        return False


async def test_sugar_beet_cercospora():
    """Test diagnosis of sugar beet cercospora leaf spot"""
    print("\n" + "="*80)
    print("TEST 3: Sugar Beet Cercospora Leaf Spot (Cercosporiose)")
    print("="*80)

    service = DiagnoseDiseaseService()

    result = await service.diagnose_disease(
        crop_type="betterave_sucrière",
        symptoms=[
            "taches_circulaires_grises",
            "bordure_brune",
            "taches_grises_centre_brun"
        ],
        environmental_conditions=EnvironmentalConditions(
            temperature_c=25.0,
            humidity_percent=80.0
        ),
        bbch_stage=39,  # Leaf development - susceptible
        field_location="Nord",
        affected_area_percent=15.0
    )

    print("\n📋 Input:")
    print(f"  Crop: Betterave sucrière (Sugar Beet)")
    print(f"  Symptoms: taches_circulaires_grises, bordure_brune")
    print(f"  BBCH Stage: 39 (Leaf development)")
    print(f"  Conditions: High humidity, warm temperature")
    print(f"  Affected Area: 15%")

    result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
    print("\n🔍 Diagnosis Result:")
    print(f"  Success: {result_dict['success']}")
    
    if result_dict['success'] and result_dict.get('diagnoses'):
        for i, diagnosis in enumerate(result_dict['diagnoses'][:3], 1):
            print(f"\n  {i}. {diagnosis['disease_name']} ({diagnosis.get('scientific_name', 'N/A')})")
            print(f"     Confidence: {diagnosis['confidence_score']:.1%}")
            print(f"     Severity: {diagnosis['severity_level']}")
            print(f"     Matched Symptoms: {len(diagnosis.get('matched_symptoms', []))}")
    else:
        print(f"  Error: {result_dict.get('error', 'Unknown error')}")
    
    # Verify Cercosporiose is top result
    if result_dict['success'] and result_dict.get('diagnoses'):
        top_disease = result_dict['diagnoses'][0]['disease_name']
        if top_disease == "Cercosporiose":
            print("\n✅ TEST PASSED: Cercosporiose correctly identified")
            return True
        else:
            print(f"\n❌ TEST FAILED: Expected 'Cercosporiose', got '{top_disease}'")
            return False
    else:
        print("\n❌ TEST FAILED: No diagnoses returned")
        return False


async def test_wheat_with_expanded_database():
    """Test that existing wheat diagnosis still works with expanded database"""
    print("\n" + "="*80)
    print("TEST 4: Wheat Septoria (Regression Test)")
    print("="*80)

    service = DiagnoseDiseaseService()

    result = await service.diagnose_disease(
        crop_type="blé",
        symptoms=[
            "taches_jaunes",
            "nécroses_feuilles",
            "pycnides_noires"
        ],
        environmental_conditions=EnvironmentalConditions(
            temperature_c=16.0,
            humidity_percent=85.0
        ),
        bbch_stage=32,
        field_location="Beauce",
        affected_area_percent=20.0
    )

    print("\n📋 Input:")
    print(f"  Crop: Blé (Wheat)")
    print(f"  Symptoms: taches_jaunes, nécroses_feuilles, pycnides_noires")
    print(f"  BBCH Stage: 32 (Tillering)")

    result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
    print("\n🔍 Diagnosis Result:")
    print(f"  Success: {result_dict['success']}")
    
    if result_dict['success'] and result_dict.get('diagnoses'):
        for i, diagnosis in enumerate(result_dict['diagnoses'][:3], 1):
            print(f"\n  {i}. {diagnosis['disease_name']}")
            print(f"     Confidence: {diagnosis['confidence_score']:.1%}")
    else:
        print(f"  Error: {result_dict.get('error', 'Unknown error')}")
    
    # Verify Septoriose is in results
    if result_dict['success'] and result_dict.get('diagnoses'):
        disease_names = [d['disease_name'] for d in result_dict['diagnoses']]
        if "Septoriose" in disease_names:
            print("\n✅ TEST PASSED: Wheat diagnosis still works correctly")
            return True
        else:
            print(f"\n❌ TEST FAILED: Septoriose not found in results")
            return False
    else:
        print("\n❌ TEST FAILED: No diagnoses returned")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING DIAGNOSE DISEASE TOOL WITH NEW CROPS")
    print("="*80)
    print("\nTesting 3 new crops + 1 regression test:")
    print("  1. Pomme de terre (Potato) - Mildiou")
    print("  2. Vigne (Grapevine) - Mildiou de la vigne")
    print("  3. Betterave sucrière (Sugar Beet) - Cercosporiose")
    print("  4. Blé (Wheat) - Septoriose (regression)")
    
    results = []
    
    try:
        results.append(await test_potato_late_blight())
        results.append(await test_grapevine_downy_mildew())
        results.append(await test_sugar_beet_cercospora())
        results.append(await test_wheat_with_expanded_database())
        
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        passed = sum(results)
        total = len(results)
        print(f"\n✅ Passed: {passed}/{total} ({passed/total*100:.0f}%)")
        print(f"❌ Failed: {total-passed}/{total}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! New crops are working correctly.")
        else:
            print("\n⚠️  Some tests failed. Review output above.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

