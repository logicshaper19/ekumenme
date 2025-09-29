#!/usr/bin/env python3
"""
Test script to verify agri_db structure and prepare for MesParcelles migration
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal


async def test_current_structure():
    """Test current agri_db structure and EPHY data."""
    print("🔍 Testing current agri_db structure...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check existing schemas
            result = await session.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name;
            """))
            schemas = [row[0] for row in result.fetchall()]
            print(f"📁 Existing schemas: {', '.join(schemas)}")
            
            # Check EPHY tables
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('produits', 'substances_actives', 'titulaires')
                ORDER BY table_name;
            """))
            ephy_tables = [row[0] for row in result.fetchall()]
            print(f"🧪 EPHY tables: {', '.join(ephy_tables)}")
            
            # Check EPHY data counts
            if 'produits' in ephy_tables:
                result = await session.execute(text("SELECT COUNT(*) FROM produits"))
                product_count = result.scalar()
                print(f"📊 EPHY products: {product_count}")
                
                result = await session.execute(text("""
                    SELECT type_produit, COUNT(*) 
                    FROM produits 
                    WHERE type_produit IS NOT NULL
                    GROUP BY type_produit 
                    ORDER BY COUNT(*) DESC
                """))
                product_types = result.fetchall()
                print("📈 Product types:")
                for ptype, count in product_types:
                    print(f"   - {ptype}: {count}")
            
            if 'substances_actives' in ephy_tables:
                result = await session.execute(text("SELECT COUNT(*) FROM substances_actives"))
                substance_count = result.scalar()
                print(f"🧬 EPHY substances: {substance_count}")
            
            # Check for any existing MesParcelles-like tables
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('exploitations', 'parcelles', 'interventions', 'cultures')
                ORDER BY table_name;
            """))
            mesparcelles_tables = [row[0] for row in result.fetchall()]
            if mesparcelles_tables:
                print(f"🚜 Existing MesParcelles tables: {', '.join(mesparcelles_tables)}")
            else:
                print("🚜 No MesParcelles tables found (ready for migration)")
            
            print("\n✅ Database structure analysis complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error testing database structure: {e}")
            return False


async def test_ephy_integration_readiness():
    """Test if EPHY data is ready for integration."""
    print("\n🔗 Testing EPHY integration readiness...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        try:
            # Test AMM code samples
            result = await session.execute(text("""
                SELECT numero_amm, nom_produit, type_produit, mentions_autorisees
                FROM produits 
                WHERE numero_amm IS NOT NULL 
                AND LENGTH(numero_amm) > 0
                LIMIT 5
            """))
            amm_samples = result.fetchall()
            
            print("🏷️ Sample AMM codes for integration:")
            for amm, nom, type_prod, mentions in amm_samples:
                print(f"   - {amm}: {nom} ({type_prod})")
                if mentions:
                    print(f"     Mentions: {mentions[:50]}...")
            
            # Test products with garden authorization
            result = await session.execute(text("""
                SELECT COUNT(*) 
                FROM produits 
                WHERE mentions_autorisees LIKE '%jardins%'
            """))
            garden_count = result.scalar()
            print(f"🌱 Products authorized for gardens: {garden_count}")
            
            # Test products with organic authorization
            result = await session.execute(text("""
                SELECT COUNT(*) 
                FROM produits 
                WHERE mentions_autorisees LIKE '%biologique%'
            """))
            organic_count = result.scalar()
            print(f"🌿 Products authorized for organic farming: {organic_count}")
            
            print("\n✅ EPHY integration readiness confirmed!")
            return True
            
        except Exception as e:
            print(f"❌ Error testing EPHY integration: {e}")
            return False


async def create_sample_integration_query():
    """Create a sample query showing future integration possibilities."""
    print("\n📝 Sample integration query (for after MesParcelles migration):")
    print("=" * 70)
    
    sample_query = """
    -- This query will be possible after MesParcelles migration:
    SELECT 
        e.nom as exploitation,
        i.date_debut,
        inp.libelle as produit_utilise,
        p.nom_produit as produit_ephy,
        p.mentions_autorisees,
        ii.quantite_totale,
        ii.unite_intrant_intervention,
        CASE 
            WHEN p.mentions_autorisees LIKE '%jardins%' THEN 'Garden Authorized'
            WHEN p.mentions_autorisees LIKE '%biologique%' THEN 'Organic Authorized'
            ELSE 'Standard Use'
        END as authorization_type
    FROM farm_operations.exploitations e
    JOIN farm_operations.interventions i ON e.siret = i.siret_exploitation
    JOIN farm_operations.intervention_intrants ii ON i.uuid_intervention = ii.uuid_intervention
    JOIN reference.intrants inp ON ii.id_intrant = inp.id_intrant
    LEFT JOIN regulatory.produits p ON inp.code_amm = p.numero_amm
    WHERE i.date_debut >= '2024-01-01'
    ORDER BY i.date_debut DESC;
    """
    
    print(sample_query)
    print("\n🎯 This will enable:")
    print("   - Cross-referencing farm operations with regulatory data")
    print("   - Compliance checking in real-time")
    print("   - Integrated reporting across farm and regulatory domains")
    print("   - Semantic search across all agricultural data")


async def main():
    """Main test function."""
    print("🧪 AgriDB Structure Test & Migration Preparation")
    print("=" * 60)
    
    # Test current structure
    structure_ok = await test_current_structure()
    if not structure_ok:
        return False
    
    # Test EPHY integration readiness
    integration_ok = await test_ephy_integration_readiness()
    if not integration_ok:
        return False
    
    # Show sample integration possibilities
    await create_sample_integration_query()
    
    print("\n" + "=" * 60)
    print("🎉 AgriDB is ready for MesParcelles migration!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Identify your MesParcelles database connection string")
    print("2. Run: python migrate_mesparcelles_to_agri_db.py <source_db_url>")
    print("3. Verify migration with integration views")
    print("4. Update application connections to use unified agri_db")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
