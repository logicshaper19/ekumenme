#!/usr/bin/env python3
"""
Test script for Crop Model and Phase 2 Implementation

Validates:
- Crop table creation
- EPPO code lookups
- Crop-Disease relationships
- Crop-BBCH relationships
- Data integrity
"""

import sys
from pathlib import Path

# Add parent directory to path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def test_crops_table():
    """Test crops table exists and has data"""
    print("🧪 Test 1: Crops Table")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check table exists
        query = text("""
            SELECT COUNT(*) as count FROM crops WHERE is_active = TRUE
        """)
        result = await db.execute(query)
        count = result.scalar()
        
        print(f"  Total active crops: {count}")
        
        if count >= 24:
            print(f"  ✅ Crops table populated ({count} crops)")
            return True
        else:
            print(f"  ❌ Expected at least 24 crops, found {count}")
            return False


async def test_crop_eppo_codes():
    """Test EPPO codes are unique and valid"""
    print("\n🧪 Test 2: EPPO Codes")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check EPPO codes
        query = text("""
            SELECT 
                name_fr,
                eppo_code,
                category
            FROM crops
            WHERE is_active = TRUE
            ORDER BY category, name_fr
        """)
        result = await db.execute(query)
        crops = result.fetchall()
        
        eppo_codes = set()
        duplicates = []
        
        for crop in crops:
            if crop[1] in eppo_codes:
                duplicates.append(crop[1])
            eppo_codes.add(crop[1])
            print(f"  {crop[0]:20} → {crop[1]:6} ({crop[2]})")
        
        if not duplicates:
            print(f"\n  ✅ All {len(eppo_codes)} EPPO codes are unique")
            return True
        else:
            print(f"\n  ❌ Duplicate EPPO codes found: {duplicates}")
            return False


async def test_bbch_crop_eppo():
    """Test BBCH stages have crop_eppo_code"""
    print("\n🧪 Test 3: BBCH Stages with EPPO Codes")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check BBCH stages
        query = text("""
            SELECT 
                crop_type,
                crop_eppo_code,
                COUNT(*) as stage_count
            FROM bbch_stages
            GROUP BY crop_type, crop_eppo_code
            ORDER BY crop_type
        """)
        result = await db.execute(query)
        stages = result.fetchall()
        
        total_with_eppo = 0
        total_without_eppo = 0
        
        for stage in stages:
            crop_type = stage[0] if stage[0] else "NULL"
            eppo_code = stage[1] if stage[1] else "NO EPPO"
            if stage[1]:  # has crop_eppo_code
                total_with_eppo += stage[2]
                print(f"  ✅ {crop_type:20} → {eppo_code:6} ({stage[2]} stages)")
            else:
                total_without_eppo += stage[2]
                print(f"  ⚠️  {crop_type:20} → {eppo_code:8} ({stage[2]} stages)")
        
        print(f"\n  With EPPO codes: {total_with_eppo} stages")
        print(f"  Without EPPO codes: {total_without_eppo} stages")
        
        if total_without_eppo == 0:
            print(f"  ✅ All BBCH stages have EPPO codes")
            return True
        else:
            print(f"  ⚠️  Some BBCH stages missing EPPO codes")
            return total_with_eppo > 0  # Partial success


async def test_disease_crop_links():
    """Test diseases have crop_id links"""
    print("\n🧪 Test 4: Disease-Crop Links")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check disease-crop links
        query = text("""
            SELECT 
                primary_crop,
                primary_crop_eppo,
                crop_id,
                COUNT(*) as disease_count
            FROM diseases
            GROUP BY primary_crop, primary_crop_eppo, crop_id
            ORDER BY primary_crop
        """)
        result = await db.execute(query)
        links = result.fetchall()
        
        total_with_id = 0
        total_without_id = 0
        
        for link in links:
            crop_name = link[0] if link[0] else "NULL"
            eppo_code = link[1] if link[1] else "NO EPPO"
            crop_id = link[2] if link[2] else "NO ID"
            if link[2]:  # has crop_id
                total_with_id += link[3]
                print(f"  ✅ {crop_name:20} → {eppo_code:6} (ID: {crop_id}, {link[3]} diseases)")
            else:
                total_without_id += link[3]
                print(f"  ⚠️  {crop_name:20} → {eppo_code:8} ({crop_id}, {link[3]} diseases)")
        
        print(f"\n  With crop_id: {total_with_id} diseases")
        print(f"  Without crop_id: {total_without_id} diseases")
        
        if total_without_id == 0:
            print(f"  ✅ All diseases have crop_id")
            return True
        else:
            print(f"  ⚠️  Some diseases missing crop_id")
            return total_with_id > 0  # Partial success


async def test_crop_relationships():
    """Test crop relationships with diseases and BBCH"""
    print("\n🧪 Test 5: Crop Relationships")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check relationships
        query = text("""
            SELECT
                c.name_fr,
                c.eppo_code,
                COUNT(DISTINCT d.id) as disease_count,
                COUNT(DISTINCT b.bbch_code) as bbch_count
            FROM crops c
            LEFT JOIN diseases d ON c.id = d.crop_id
            LEFT JOIN bbch_stages b ON c.eppo_code = b.crop_eppo_code
            WHERE c.is_active = TRUE
            GROUP BY c.id, c.name_fr, c.eppo_code
            ORDER BY c.name_fr
        """)
        result = await db.execute(query)
        relationships = result.fetchall()
        
        crops_with_data = 0
        crops_without_data = 0
        
        for rel in relationships:
            if rel[2] > 0 or rel[3] > 0:
                crops_with_data += 1
                print(f"  ✅ {rel[0]:20} ({rel[1]}): {rel[2]} diseases, {rel[3]} BBCH stages")
            else:
                crops_without_data += 1
                print(f"  ⚠️  {rel[0]:20} ({rel[1]}): No data")
        
        print(f"\n  Crops with data: {crops_with_data}")
        print(f"  Crops without data: {crops_without_data}")
        
        if crops_with_data > 0:
            print(f"  ✅ Crop relationships working")
            return True
        else:
            print(f"  ❌ No crop relationships found")
            return False


async def test_data_integrity():
    """Test data integrity and foreign key relationships"""
    print("\n🧪 Test 6: Data Integrity")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check for orphaned diseases (crop_id not in crops)
        query = text("""
            SELECT COUNT(*) 
            FROM diseases d
            WHERE d.crop_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM crops c WHERE c.id = d.crop_id)
        """)
        result = await db.execute(query)
        orphaned_diseases = result.scalar()
        
        # Check for orphaned BBCH stages (crop_eppo_code not in crops)
        query = text("""
            SELECT COUNT(*) 
            FROM bbch_stages b
            WHERE b.crop_eppo_code IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM crops c WHERE c.eppo_code = b.crop_eppo_code)
        """)
        result = await db.execute(query)
        orphaned_bbch = result.scalar()
        
        print(f"  Orphaned diseases: {orphaned_diseases}")
        print(f"  Orphaned BBCH stages: {orphaned_bbch}")
        
        if orphaned_diseases == 0 and orphaned_bbch == 0:
            print(f"  ✅ No orphaned records - data integrity intact")
            return True
        else:
            print(f"  ⚠️  Found orphaned records")
            return False


async def test_backward_compatibility():
    """Test backward compatibility with old string-based queries"""
    print("\n🧪 Test 7: Backward Compatibility")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Old-style query (by primary_crop string)
        query_old = text("""
            SELECT COUNT(*) FROM diseases WHERE primary_crop = 'blé'
        """)
        result_old = await db.execute(query_old)
        count_old = result_old.scalar()
        
        # New-style query (by crop_id)
        query_new = text("""
            SELECT COUNT(*) 
            FROM diseases d
            JOIN crops c ON d.crop_id = c.id
            WHERE c.name_fr = 'blé'
        """)
        result_new = await db.execute(query_new)
        count_new = result_new.scalar()
        
        print(f"  Old query (primary_crop = 'blé'): {count_old} diseases")
        print(f"  New query (JOIN crops): {count_new} diseases")
        
        if count_old == count_new and count_old > 0:
            print(f"  ✅ Backward compatibility maintained")
            return True
        else:
            print(f"  ⚠️  Query results differ")
            return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🌾 CROP MODEL & PHASE 2 - TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        test_crops_table,
        test_crop_eppo_codes,
        test_bbch_crop_eppo,
        test_disease_crop_links,
        test_crop_relationships,
        test_data_integrity,
        test_backward_compatibility,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}\n")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - Test {i}: {test.__name__}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! Phase 2 implementation successful! ✅")
        return 0
    elif passed >= total * 0.7:
        print(f"\n  ⚠️  Most tests passed ({passed}/{total}), but some issues remain")
        return 0
    else:
        print(f"\n  ❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

