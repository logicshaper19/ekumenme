#!/usr/bin/env python3
"""
Test script for Crop EPPO Codes implementation

Validates:
- EPPO code lookups
- Crop name validation
- Bidirectional mapping
- Alias support
- Error handling
"""

import sys
from pathlib import Path

# Add parent directory to path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.constants.crop_eppo_codes import (
    get_eppo_code,
    get_crop_name,
    validate_crop,
    validate_crop_strict,
    normalize_crop_name,
    get_all_crops,
    get_crop_category,
    get_crops_by_category,
    CropCategory,
    CROP_EPPO_CODES
)


def test_basic_lookups():
    """Test basic EPPO code lookups"""
    print("🧪 Test 1: Basic EPPO Code Lookups")
    print("="*60)
    
    test_cases = [
        ("blé", "TRZAX"),
        ("maïs", "ZEAMX"),
        ("colza", "BRSNN"),
        ("orge", "HORVX"),
        ("tournesol", "HELAN"),
        ("pomme de terre", "SOLTU"),
    ]
    
    passed = 0
    for crop, expected_eppo in test_cases:
        result = get_eppo_code(crop)
        status = "✅" if result == expected_eppo else "❌"
        print(f"  {status} {crop:20} → {result} (expected: {expected_eppo})")
        if result == expected_eppo:
            passed += 1
    
    print(f"\n  Result: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_reverse_lookups():
    """Test reverse lookups (EPPO → crop name)"""
    print("🧪 Test 2: Reverse Lookups (EPPO → Crop Name)")
    print("="*60)
    
    test_cases = [
        ("TRZAX", "blé"),
        ("ZEAMX", "maïs"),
        ("BRSNN", "colza"),
        ("HORVX", "orge"),
        ("HELAN", "tournesol"),
    ]
    
    passed = 0
    for eppo, expected_crop in test_cases:
        result = get_crop_name(eppo)
        status = "✅" if result == expected_crop else "❌"
        print(f"  {status} {eppo:10} → {result} (expected: {expected_crop})")
        if result == expected_crop:
            passed += 1
    
    print(f"\n  Result: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_aliases():
    """Test crop name aliases"""
    print("🧪 Test 3: Crop Name Aliases")
    print("="*60)
    
    test_cases = [
        ("ble", "blé", "TRZAX"),      # No accent
        ("mais", "maïs", "ZEAMX"),    # No accent
        ("wheat", "blé", "TRZAX"),    # English
        ("corn", "maïs", "ZEAMX"),    # English
        ("potato", "pomme de terre", "SOLTU"),  # English
    ]
    
    passed = 0
    for alias, expected_normalized, expected_eppo in test_cases:
        normalized = normalize_crop_name(alias)
        eppo = get_eppo_code(alias)
        
        if normalized == expected_normalized and eppo == expected_eppo:
            print(f"  ✅ '{alias}' → '{normalized}' → {eppo}")
            passed += 1
        else:
            print(f"  ❌ '{alias}' → '{normalized}' → {eppo} (expected: '{expected_normalized}' → {expected_eppo})")
    
    print(f"\n  Result: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_validation():
    """Test crop validation"""
    print("🧪 Test 4: Crop Validation")
    print("="*60)
    
    valid_crops = ["blé", "maïs", "colza", "orge"]
    invalid_crops = ["invalid_crop", "xyz", ""]
    
    passed = 0
    total = len(valid_crops) + len(invalid_crops)
    
    # Test valid crops
    for crop in valid_crops:
        is_valid = validate_crop(crop)
        status = "✅" if is_valid else "❌"
        print(f"  {status} validate_crop('{crop}') = {is_valid} (expected: True)")
        if is_valid:
            passed += 1
    
    # Test invalid crops
    for crop in invalid_crops:
        is_valid = validate_crop(crop)
        status = "✅" if not is_valid else "❌"
        print(f"  {status} validate_crop('{crop}') = {is_valid} (expected: False)")
        if not is_valid:
            passed += 1
    
    print(f"\n  Result: {passed}/{total} passed\n")
    return passed == total


def test_strict_validation():
    """Test strict validation with error handling"""
    print("🧪 Test 5: Strict Validation (Error Handling)")
    print("="*60)
    
    passed = 0
    
    # Should succeed
    try:
        result = validate_crop_strict("blé")
        print(f"  ✅ validate_crop_strict('blé') = '{result}'")
        passed += 1
    except ValueError as e:
        print(f"  ❌ validate_crop_strict('blé') raised error: {e}")
    
    # Should fail
    try:
        result = validate_crop_strict("invalid_crop")
        print(f"  ❌ validate_crop_strict('invalid_crop') should have raised ValueError, got: '{result}'")
    except ValueError as e:
        print(f"  ✅ validate_crop_strict('invalid_crop') correctly raised ValueError")
        passed += 1
    
    print(f"\n  Result: {passed}/2 passed\n")
    return passed == 2


def test_categories():
    """Test crop categories"""
    print("🧪 Test 6: Crop Categories")
    print("="*60)
    
    test_cases = [
        ("blé", CropCategory.CEREAL),
        ("maïs", CropCategory.CEREAL),
        ("colza", CropCategory.OILSEED),
        ("tournesol", CropCategory.OILSEED),
        ("betterave", CropCategory.ROOT_CROP),
        ("pois", CropCategory.LEGUME),
        ("vigne", CropCategory.FRUIT),
    ]
    
    passed = 0
    for crop, expected_category in test_cases:
        result = get_crop_category(crop)
        status = "✅" if result == expected_category else "❌"
        print(f"  {status} {crop:15} → {result} (expected: {expected_category})")
        if result == expected_category:
            passed += 1
    
    print(f"\n  Result: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_category_filtering():
    """Test filtering crops by category"""
    print("🧪 Test 7: Filter Crops by Category")
    print("="*60)
    
    cereals = get_crops_by_category(CropCategory.CEREAL)
    oilseeds = get_crops_by_category(CropCategory.OILSEED)
    
    print(f"  Cereals ({len(cereals)}): {', '.join(cereals)}")
    print(f"  Oilseeds ({len(oilseeds)}): {', '.join(oilseeds)}")
    
    # Basic validation
    passed = 0
    if "blé" in cereals and "maïs" in cereals:
        print("  ✅ Cereals contain blé and maïs")
        passed += 1
    else:
        print("  ❌ Cereals missing expected crops")
    
    if "colza" in oilseeds and "tournesol" in oilseeds:
        print("  ✅ Oilseeds contain colza and tournesol")
        passed += 1
    else:
        print("  ❌ Oilseeds missing expected crops")
    
    print(f"\n  Result: {passed}/2 passed\n")
    return passed == 2


def test_completeness():
    """Test data completeness"""
    print("🧪 Test 8: Data Completeness")
    print("="*60)
    
    all_crops = get_all_crops()
    print(f"  Total crops defined: {len(all_crops)}")
    print(f"  Crops: {', '.join(sorted(all_crops))}")
    
    # Check bidirectional mapping
    passed = 0
    total = len(all_crops)
    
    for crop in all_crops:
        eppo = get_eppo_code(crop)
        reverse = get_crop_name(eppo)
        
        if reverse == crop:
            passed += 1
        else:
            print(f"  ❌ Bidirectional mapping failed: {crop} → {eppo} → {reverse}")
    
    if passed == total:
        print(f"  ✅ All {total} crops have valid bidirectional mapping")
    else:
        print(f"  ❌ Only {passed}/{total} crops have valid bidirectional mapping")
    
    print(f"\n  Result: {passed}/{total} passed\n")
    return passed == total


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🌾 CROP EPPO CODES - TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        test_basic_lookups,
        test_reverse_lookups,
        test_aliases,
        test_validation,
        test_strict_validation,
        test_categories,
        test_category_filtering,
        test_completeness,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}\n")
            results.append(False)
    
    # Summary
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - Test {i}: {test.__name__}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! ✅")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

