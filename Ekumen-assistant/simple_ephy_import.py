#!/usr/bin/env python3
"""
Simplified EPHY Data Import Script for Ekumen-assistant
Imports basic EPHY product data from CSV files into the database (without PostGIS)
"""

import asyncio
import pandas as pd
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal, async_engine
from app.models.ephy import SubstanceActive, Titulaire, Produit


class SimpleEPHYImporter:
    """Simplified EPHY data importer for Ekumen-assistant."""
    
    def __init__(self):
        self.stats = {
            "substances": 0,
            "titulaires": 0,
            "products": 0,
            "errors": []
        }
    
    async def create_tables(self):
        """Create only EPHY database tables (avoiding PostGIS dependencies)."""
        try:
            from sqlalchemy import MetaData

            # Create EPHY-only metadata
            ephy_metadata = MetaData()

            # Add only EPHY tables to avoid PostGIS dependencies
            ephy_tables = [
                SubstanceActive.__table__,
                Titulaire.__table__,
                Produit.__table__
            ]

            for table in ephy_tables:
                table.tometadata(ephy_metadata)

            # Drop existing tables to ensure clean schema
            async with async_engine.begin() as conn:
                await conn.run_sync(ephy_metadata.drop_all)
                await conn.run_sync(ephy_metadata.create_all)
            print("✅ EPHY database tables recreated successfully")

            # Add missing enum values
            await self.add_missing_enum_values()
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise
    
    async def test_connection(self):
        """Test database connection."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                print("✅ Database connection successful")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    async def add_missing_enum_values(self):
        """Add missing enum values to existing enums."""
        try:
            async with async_engine.begin() as conn:
                # Add missing values to ProductType enum if they don't exist
                await conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ADJUVANT' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'producttype')) THEN
                            ALTER TYPE producttype ADD VALUE 'ADJUVANT';
                        END IF;
                        -- Note: Database enum uses PRODUIT_MIXTE (normalized from CSV PRODUIT-MIXTE)
                        IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'PRODUIT_MIXTE' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'producttype')) THEN
                            ALTER TYPE producttype ADD VALUE 'PRODUIT_MIXTE';
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'MELANGE' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'producttype')) THEN
                            ALTER TYPE producttype ADD VALUE 'MELANGE';
                        END IF;
                    END $$;
                """))
                print("✅ Added missing enum values")
        except Exception as e:
            print(f"⚠️ Warning: Could not add enum values: {e}")
            # Don't raise - this is not critical

    def _normalize_product_type(self, product_type: str) -> str:
        """Normalize product type from CSV to database enum format."""
        if not product_type:
            return None
        # Convert CSV format to database enum format
        if product_type == "PRODUIT-MIXTE":
            return "PRODUIT_MIXTE"
        return product_type

    async def import_substances(self, csv_path: str):
        """Import active substances from CSV."""
        if not os.path.exists(csv_path):
            print(f"⚠️  Substances CSV not found: {csv_path}")
            return
        
        try:
            df = pd.read_csv(csv_path, sep=';', encoding='windows-1252')
            print(f"📊 Found {len(df)} substances to import")
            
            async with AsyncSessionLocal() as session:
                for _, row in df.iterrows():
                    substance = SubstanceActive(
                        nom_substance=str(row.get('nom_substance', '')),
                        numero_cas=str(row.get('numero_cas', '')) if pd.notna(row.get('numero_cas')) else None,
                        etat_autorisation=str(row.get('etat_autorisation', '')) if pd.notna(row.get('etat_autorisation')) else None
                    )
                    session.add(substance)
                    self.stats["substances"] += 1
                
                await session.commit()
                print(f"✅ Imported {self.stats['substances']} substances")
        
        except Exception as e:
            print(f"❌ Error importing substances: {e}")
            self.stats["errors"].append(f"Substances: {e}")
    
    async def import_titulaires(self, csv_path: str):
        """Import titulaires from CSV."""
        if not os.path.exists(csv_path):
            print(f"⚠️  Titulaires CSV not found: {csv_path}")
            return
        
        try:
            df = pd.read_csv(csv_path, sep=';', encoding='windows-1252')
            print(f"📊 Found {len(df)} titulaires to import")
            
            async with AsyncSessionLocal() as session:
                for _, row in df.iterrows():
                    titulaire = Titulaire(
                        nom_titulaire=str(row.get('nom_titulaire', '')),
                        numero_titulaire=str(row.get('numero_titulaire', '')) if pd.notna(row.get('numero_titulaire')) else None
                    )
                    session.add(titulaire)
                    self.stats["titulaires"] += 1
                
                await session.commit()
                print(f"✅ Imported {self.stats['titulaires']} titulaires")
        
        except Exception as e:
            print(f"❌ Error importing titulaires: {e}")
            self.stats["errors"].append(f"Titulaires: {e}")
    
    async def import_products(self, csv_path: str):
        """Import products from CSV."""
        if not os.path.exists(csv_path):
            print(f"⚠️  Products CSV not found: {csv_path}")
            return
        
        try:
            df = pd.read_csv(csv_path, sep=';', encoding='windows-1252')
            print(f"📊 Found {len(df)} products to import")
            
            # Use merge to handle duplicates gracefully
            async with AsyncSessionLocal() as session:
                unique_products = {}

                # First, collect unique products by AMM number
                for _, row in df.iterrows():
                    amm_number = str(row.get('numero AMM', ''))
                    if amm_number and amm_number not in unique_products:
                        unique_products[amm_number] = {
                            'numero_amm': amm_number,
                            'nom_produit': str(row.get('nom produit', '')),
                            'type_produit': self._normalize_product_type(str(row.get('type produit', '')) if pd.notna(row.get('type produit')) else None),
                            'seconds_noms_commerciaux': str(row.get('seconds noms commerciaux', '')) if pd.notna(row.get('seconds noms commerciaux')) else None,
                            'mentions_autorisees': str(row.get('mentions autorisees', '')) if pd.notna(row.get('mentions autorisees')) else None,
                            'restrictions_usage': str(row.get('restrictions usage', '')) if pd.notna(row.get('restrictions usage')) else None,
                            'restrictions_usage_libelle': str(row.get('restrictions usage libelle', '')) if pd.notna(row.get('restrictions usage libelle')) else None,
                            'numero_amm_reference': str(row.get('Numéro AMM du produit de référence', '')) if pd.notna(row.get('Numéro AMM du produit de référence')) else None,
                            'nom_produit_reference': str(row.get('Nom du produit de référence', '')) if pd.notna(row.get('Nom du produit de référence')) else None
                        }

                # Then insert unique products using merge
                for product_data in unique_products.values():
                    product = Produit(**product_data)
                    await session.merge(product)
                    self.stats["products"] += 1

                await session.commit()
                print(f"✅ Imported {self.stats['products']} products")
        
        except Exception as e:
            print(f"❌ Error importing products: {e}")
            self.stats["errors"].append(f"Products: {e}")
    
    async def import_from_directory(self, data_dir: str):
        """Import EPHY data from directory containing CSV files."""
        print(f"🚀 Starting EPHY import from: {data_dir}")
        
        # Test connection first
        if not await self.test_connection():
            return False
        
        # Create tables
        await self.create_tables()
        
        # Look for CSV files
        csv_files = list(Path(data_dir).glob("*.csv"))
        print(f"📁 Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            filename = csv_file.name.lower()
            print(f"📄 Processing: {csv_file.name}")
            
            if 'substance' in filename:
                await self.import_substances(str(csv_file))
            elif 'titulaire' in filename:
                await self.import_titulaires(str(csv_file))
            elif 'produit' in filename:
                await self.import_products(str(csv_file))
            else:
                print(f"⏭️  Skipping unknown file: {csv_file.name}")
        
        return True
    
    def print_summary(self):
        """Print import summary."""
        print("\n" + "="*50)
        print("📊 EPHY Import Summary")
        print("="*50)
        print(f"✅ Substances imported: {self.stats['substances']}")
        print(f"✅ Titulaires imported: {self.stats['titulaires']}")
        print(f"✅ Products imported: {self.stats['products']}")
        
        if self.stats["errors"]:
            print(f"❌ Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                print(f"   - {error}")
        else:
            print("✅ No errors!")
        print("="*50)


async def main():
    """Main function."""
    print("🌾 Simple EPHY Data Importer for Ekumen-assistant")
    print("="*50)
    
    # Look for EPHY data directory
    possible_paths = [
        "Ekumenbackend/data/ephy",
        "../Ekumenbackend/data/ephy",
        "data/ephy",
        "ephy_data"
    ]
    
    data_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            data_dir = path
            break
    
    if not data_dir:
        print("❌ EPHY data directory not found. Please ensure CSV files are available.")
        print("   Expected locations:")
        for path in possible_paths:
            print(f"   - {path}")
        return
    
    importer = SimpleEPHYImporter()
    success = await importer.import_from_directory(data_dir)
    
    if success:
        importer.print_summary()
        print("🎉 EPHY import completed!")
    else:
        print("❌ EPHY import failed!")


if __name__ == "__main__":
    asyncio.run(main())
