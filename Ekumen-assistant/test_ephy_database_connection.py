#!/usr/bin/env python3
"""
Test EPHY database connection and verify data migration
Tests if Ekumen-assistant can connect to Ekumenbackend database and access EPHY data
"""

import sys
import os
import asyncio
from typing import List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from core.database import AsyncSessionLocal
from models.ephy import Produit, SubstanceActive, ProduitSubstance, UsageProduit
from sqlalchemy import select, func, text

async def test_database_connection():
    """Test basic database connection"""
    print("🔌 Testing database connection...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Test basic connection
            result = await db.execute(text("SELECT 1"))
            connection_test = result.scalar()
            
            if connection_test == 1:
                print("  ✅ Database connection successful")
                return True
            else:
                print("  ❌ Database connection failed")
                return False
                
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False

async def test_ephy_tables_exist():
    """Test if EPHY tables exist in the database"""
    print("\n📋 Testing EPHY table existence...")
    
    tables_to_check = [
        "produits",
        "substances_actives", 
        "produit_substances",
        "usages_produits",
        "titulaires"
    ]
    
    try:
        async with AsyncSessionLocal() as db:
            existing_tables = []
            missing_tables = []
            
            for table in tables_to_check:
                try:
                    result = await db.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        )
                    """))
                    exists = result.scalar()
                    
                    if exists:
                        existing_tables.append(table)
                        print(f"  ✅ Table '{table}' exists")
                    else:
                        missing_tables.append(table)
                        print(f"  ❌ Table '{table}' missing")
                        
                except Exception as e:
                    missing_tables.append(table)
                    print(f"  ❌ Error checking table '{table}': {e}")
            
            print(f"\n  📊 Summary: {len(existing_tables)}/{len(tables_to_check)} tables exist")
            return len(missing_tables) == 0
            
    except Exception as e:
        print(f"  ❌ Error checking tables: {e}")
        return False

async def test_ephy_data_count():
    """Test if EPHY data exists in the database"""
    print("\n📊 Testing EPHY data counts...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Count products
            try:
                result = await db.execute(select(func.count(Produit.numero_amm)))
                product_count = result.scalar()
                print(f"  📦 Products: {product_count:,}")
            except Exception as e:
                print(f"  ❌ Error counting products: {e}")
                product_count = 0
            
            # Count substances
            try:
                result = await db.execute(select(func.count(SubstanceActive.id)))
                substance_count = result.scalar()
                print(f"  🧪 Active substances: {substance_count:,}")
            except Exception as e:
                print(f"  ❌ Error counting substances: {e}")
                substance_count = 0
            
            # Count usages
            try:
                result = await db.execute(select(func.count(UsageProduit.id)))
                usage_count = result.scalar()
                print(f"  📋 Product usages: {usage_count:,}")
            except Exception as e:
                print(f"  ❌ Error counting usages: {e}")
                usage_count = 0
            
            # Check if we have meaningful data
            has_data = product_count > 1000 and substance_count > 100
            
            if has_data:
                print(f"\n  ✅ EPHY database contains substantial data")
                print(f"     Expected: ~30,000 products, ~1,000 substances")
                print(f"     Found: {product_count:,} products, {substance_count:,} substances")
            else:
                print(f"\n  ⚠️  EPHY database appears to have limited data")
                print(f"     Found: {product_count:,} products, {substance_count:,} substances")
                print(f"     Expected: ~30,000 products, ~1,000 substances")
            
            return has_data
            
    except Exception as e:
        print(f"  ❌ Error checking data counts: {e}")
        return False

async def test_sample_ephy_queries():
    """Test sample EPHY queries to verify data structure"""
    print("\n🔍 Testing sample EPHY queries...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Test 1: Get a few products
            try:
                result = await db.execute(
                    select(Produit.numero_amm, Produit.nom_produit, Produit.type_produit)
                    .where(Produit.etat_autorisation == 'AUTORISE')
                    .limit(5)
                )
                products = result.all()
                
                print(f"  📦 Sample authorized products:")
                for product in products:
                    print(f"     • {product.numero_amm}: {product.nom_produit} ({product.type_produit})")
                
            except Exception as e:
                print(f"  ❌ Error querying products: {e}")
            
            # Test 2: Get a few substances
            try:
                result = await db.execute(
                    select(SubstanceActive.nom_substance)
                    .limit(5)
                )
                substances = result.scalars().all()
                
                print(f"  🧪 Sample active substances:")
                for substance in substances:
                    print(f"     • {substance}")
                
            except Exception as e:
                print(f"  ❌ Error querying substances: {e}")
            
            # Test 3: Test join query (product with substances)
            try:
                result = await db.execute(
                    select(Produit.nom_produit, SubstanceActive.nom_substance)
                    .join(ProduitSubstance, Produit.numero_amm == ProduitSubstance.numero_amm)
                    .join(SubstanceActive, ProduitSubstance.substance_id == SubstanceActive.id)
                    .limit(3)
                )
                product_substances = result.all()
                
                print(f"  🔗 Sample product-substance relationships:")
                for prod_sub in product_substances:
                    print(f"     • {prod_sub.nom_produit} contains {prod_sub.nom_substance}")
                
                return True
                
            except Exception as e:
                print(f"  ❌ Error testing join queries: {e}")
                return False
            
    except Exception as e:
        print(f"  ❌ Error in sample queries: {e}")
        return False

async def test_amm_lookup_functionality():
    """Test AMM lookup functionality with real data"""
    print("\n🔎 Testing AMM lookup functionality...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Search for a common herbicide
            search_terms = ["glyphosate", "roundup", "herbicide"]
            
            for term in search_terms:
                try:
                    # Search by product name
                    result = await db.execute(
                        select(Produit.numero_amm, Produit.nom_produit)
                        .where(Produit.nom_produit.ilike(f"%{term}%"))
                        .where(Produit.etat_autorisation == 'AUTORISE')
                        .limit(3)
                    )
                    products = result.all()
                    
                    if products:
                        print(f"  🔍 Search for '{term}' found {len(products)} products:")
                        for product in products:
                            print(f"     • {product.numero_amm}: {product.nom_produit}")
                    else:
                        print(f"  ⚠️  No products found for search term '{term}'")
                        
                except Exception as e:
                    print(f"  ❌ Error searching for '{term}': {e}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error in AMM lookup test: {e}")
        return False

async def run_all_tests():
    """Run comprehensive EPHY database tests"""
    print("🧪 EPHY Database Connection Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("EPHY Tables Existence", test_ephy_tables_exist),
        ("EPHY Data Counts", test_ephy_data_count),
        ("Sample EPHY Queries", test_sample_ephy_queries),
        ("AMM Lookup Functionality", test_amm_lookup_functionality)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"\n❌ ERROR in {test_name}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All tests passed! EPHY database is properly connected and populated.")
        print("\n📋 Next Steps:")
        print("  1. ✅ Database connection working")
        print("  2. ✅ EPHY tables accessible") 
        print("  3. ✅ EPHY data available")
        print("  4. ✅ AMM lookup functionality ready")
        print("\n🚀 Ekumen-assistant is ready to use real EPHY data!")
    else:
        print("⚠️  Some tests failed. EPHY database migration may be incomplete.")
        print("\n📋 Possible Issues:")
        if not results.get("Database Connection"):
            print("  • Check database connection settings")
            print("  • Verify Ekumenbackend is running")
        if not results.get("EPHY Tables Existence"):
            print("  • EPHY tables may not be created")
            print("  • Run EPHY import in Ekumenbackend")
        if not results.get("EPHY Data Counts"):
            print("  • EPHY data may not be imported")
            print("  • Check EPHY CSV import process")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
