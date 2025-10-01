#!/usr/bin/env python3
"""
EPHY Data Import Script for Ekumen-assistant
Imports EPHY data from CSV files into the database
"""

import sys
import os
import asyncio
import pandas as pd
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from core.database import AsyncSessionLocal, async_engine
from models.ephy import (
    Base, Produit, SubstanceActive, ProduitSubstance, UsageProduit,
    Titulaire, Formulation, Fonction, ProduitFonction, ProduitFormulation,
    PhraseRisque, ProduitPhraseRisque, ProduitClassification, ConditionEmploi,
    PermisImportation, ProductType, CommercialType, GammeUsage, EtatAutorisation
)
from sqlalchemy import select, text


class EPHYImporter:
    """EPHY data importer for Ekumen-assistant."""
    
    def __init__(self):
        self.stats = {
            "produits": 0,
            "substances": 0,
            "titulaires": 0,
            "usages": 0,
            "classifications": 0,
            "conditions": 0,
            "phrases_risque": 0,
            "permis": 0,
            "errors": []
        }
    
    async def create_tables(self):
        """Create all EPHY tables."""
        print("🏗️  Creating EPHY database tables...")
        
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ EPHY tables created successfully")
    
    async def import_from_zip(self, zip_path: str) -> Dict[str, Any]:
        """Import EPHY data from ZIP file."""
        print(f"📦 Extracting ZIP file: {zip_path}")
        
        # Extract ZIP file
        extract_path = Path(zip_path).parent / "extracted"
        extract_path.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Find CSV files
        csv_files = list(extract_path.glob("*.csv"))
        print(f"📄 Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            print(f"   • {csv_file.name}")
        
        # Import data in order
        await self._import_substances(extract_path)
        await self._import_titulaires(extract_path)
        await self._import_produits(extract_path)
        await self._import_usages(extract_path)
        await self._import_classifications(extract_path)
        await self._import_conditions(extract_path)
        await self._import_phrases_risque(extract_path)
        await self._import_permis(extract_path)
        
        return self.stats
    
    async def _import_substances(self, extract_path: Path):
        """Import active substances from file 9."""
        print("\n🧪 Importing active substances...")
        
        # Find the substances file (file 9)
        csv_files = list(extract_path.glob("*.csv"))
        substances_file = None
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, sep=';', encoding='windows-1252', nrows=5)
                if 'Nom substance active' in df.columns:
                    substances_file = csv_file
                    break
            except:
                continue
        
        if not substances_file:
            print("⚠️  Substances file not found")
            return
        
        print(f"📄 Reading: {substances_file.name}")
        df = pd.read_csv(substances_file, sep=';', encoding='windows-1252')
        
        async with AsyncSessionLocal() as db:
            for _, row in df.iterrows():
                try:
                    substance = SubstanceActive(
                        nom_substance=str(row.get('Nom substance active', '')),
                        numero_cas=str(row.get('Numero CAS', '')) if pd.notna(row.get('Numero CAS')) else None,
                        etat_autorisation=str(row.get('Etat d\'autorisation', '')),
                        variants=str(row.get('Variant', '')) if pd.notna(row.get('Variant')) else None
                    )
                    db.add(substance)
                    self.stats["substances"] += 1
                    
                except Exception as e:
                    self.stats["errors"].append(f"Substance error: {e}")
            
            await db.commit()
        
        print(f"✅ Imported {self.stats['substances']} substances")
    
    async def _import_titulaires(self, extract_path: Path):
        """Import titulaires from product files."""
        print("\n🏢 Importing titulaires...")
        
        # Find the main products file (file 8)
        csv_files = list(extract_path.glob("*.csv"))
        products_file = None
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, sep=';', encoding='windows-1252', nrows=5)
                if 'titulaire' in df.columns and 'Substances actives' in df.columns:
                    products_file = csv_file
                    break
            except:
                continue
        
        if not products_file:
            print("⚠️  Products file not found")
            return
        
        print(f"📄 Reading: {products_file.name}")
        df = pd.read_csv(products_file, sep=';', encoding='windows-1252')
        
        # Get unique titulaires
        titulaires_set = set()
        for _, row in df.iterrows():
            titulaire_name = str(row.get('titulaire', '')).strip()
            if titulaire_name and titulaire_name != 'nan':
                titulaires_set.add(titulaire_name)
        
        async with AsyncSessionLocal() as db:
            for titulaire_name in titulaires_set:
                try:
                    # Check if already exists
                    result = await db.execute(
                        select(Titulaire).where(Titulaire.nom == titulaire_name)
                    )
                    if result.scalar_one_or_none():
                        continue
                    
                    titulaire = Titulaire(nom=titulaire_name)
                    db.add(titulaire)
                    self.stats["titulaires"] += 1
                    
                except Exception as e:
                    self.stats["errors"].append(f"Titulaire error: {e}")
            
            await db.commit()
        
        print(f"✅ Imported {self.stats['titulaires']} titulaires")
    
    async def _import_produits(self, extract_path: Path):
        """Import products from file 8."""
        print("\n📦 Importing products...")
        
        # Find the main products file (file 8)
        csv_files = list(extract_path.glob("*.csv"))
        products_file = None
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, sep=';', encoding='windows-1252', nrows=5)
                if 'titulaire' in df.columns and 'Substances actives' in df.columns:
                    products_file = csv_file
                    break
            except:
                continue
        
        if not products_file:
            print("⚠️  Products file not found")
            return
        
        print(f"📄 Reading: {products_file.name}")
        df = pd.read_csv(products_file, sep=';', encoding='windows-1252')
        
        async with AsyncSessionLocal() as db:
            # Get titulaires mapping
            result = await db.execute(select(Titulaire))
            titulaires = {t.nom: t.id for t in result.scalars().all()}
            
            for _, row in df.iterrows():
                try:
                    numero_amm = str(row.get('numero AMM', '')).strip()
                    if not numero_amm or numero_amm == 'nan':
                        continue
                    
                    # Check if already exists
                    result = await db.execute(
                        select(Produit).where(Produit.numero_amm == numero_amm)
                    )
                    if result.scalar_one_or_none():
                        continue
                    
                    titulaire_name = str(row.get('titulaire', '')).strip()
                    titulaire_id = titulaires.get(titulaire_name)
                    
                    # Parse type_produit
                    type_produit = None
                    type_str = str(row.get('type produit', '')).strip().upper()
                    if type_str in ['PPP', 'MFSC']:
                        type_produit = ProductType(type_str)
                    
                    # Parse type_commercial
                    type_commercial = None
                    type_comm_str = str(row.get('type commercial', '')).strip()
                    if type_comm_str in [e.value for e in CommercialType]:
                        type_commercial = CommercialType(type_comm_str)
                    
                    # Parse gamme_usage
                    gamme_usage = None
                    gamme_str = str(row.get('gamme usage', '')).strip()
                    if gamme_str in [e.value for e in GammeUsage]:
                        gamme_usage = GammeUsage(gamme_str)
                    
                    # Parse etat_autorisation
                    etat_autorisation = None
                    etat_str = str(row.get('Etat d\'autorisation', '')).strip().upper()
                    if etat_str in [e.value for e in EtatAutorisation]:
                        etat_autorisation = EtatAutorisation(etat_str)
                    
                    produit = Produit(
                        numero_amm=numero_amm,
                        nom_produit=str(row.get('nom produit', '')),
                        type_produit=type_produit,
                        seconds_noms_commerciaux=str(row.get('seconds noms commerciaux', '')) if pd.notna(row.get('seconds noms commerciaux')) else None,
                        titulaire_id=titulaire_id,
                        type_commercial=type_commercial,
                        gamme_usage=gamme_usage,
                        mentions_autorisees=str(row.get('mentions autorisees', '')) if pd.notna(row.get('mentions autorisees')) else None,
                        restrictions_usage=str(row.get('restrictions usage', '')) if pd.notna(row.get('restrictions usage')) else None,
                        restrictions_usage_libelle=str(row.get('restrictions usage libelle', '')) if pd.notna(row.get('restrictions usage libelle')) else None,
                        etat_autorisation=etat_autorisation,
                        date_retrait_produit=pd.to_datetime(row.get('Date de retrait du produit'), errors='coerce').date() if pd.notna(row.get('Date de retrait du produit')) else None,
                        date_premiere_autorisation=pd.to_datetime(row.get('Date de première autorisation'), errors='coerce').date() if pd.notna(row.get('Date de première autorisation')) else None,
                        numero_amm_reference=str(row.get('Numéro AMM du produit de référence', '')) if pd.notna(row.get('Numéro AMM du produit de référence')) else None,
                        nom_produit_reference=str(row.get('Nom du produit de référence', '')) if pd.notna(row.get('Nom du produit de référence')) else None
                    )
                    
                    db.add(produit)
                    self.stats["produits"] += 1
                    
                except Exception as e:
                    self.stats["errors"].append(f"Product error: {e}")
            
            await db.commit()
        
        print(f"✅ Imported {self.stats['produits']} products")
    
    async def _import_usages(self, extract_path: Path):
        """Import usage data from files 2, 7, 10."""
        print("\n📋 Importing usage data...")
        # Implementation would continue here...
        print("⚠️  Usage import not yet implemented")
    
    async def _import_classifications(self, extract_path: Path):
        """Import classifications from file 4."""
        print("\n🏷️  Importing classifications...")
        # Implementation would continue here...
        print("⚠️  Classifications import not yet implemented")
    
    async def _import_conditions(self, extract_path: Path):
        """Import conditions from file 5."""
        print("\n⚠️  Importing conditions...")
        # Implementation would continue here...
        print("⚠️  Conditions import not yet implemented")
    
    async def _import_phrases_risque(self, extract_path: Path):
        """Import risk phrases from file 6."""
        print("\n⚠️  Importing risk phrases...")
        # Implementation would continue here...
        print("⚠️  Risk phrases import not yet implemented")
    
    async def _import_permis(self, extract_path: Path):
        """Import import permits from file 3."""
        print("\n📄 Importing import permits...")
        # Implementation would continue here...
        print("⚠️  Import permits not yet implemented")


async def main():
    """Main import function."""
    print("🌾 EPHY Data Import for Ekumen-assistant")
    print("=" * 50)
    
    # Path to the EPHY ZIP file
    zip_path = "/Users/elisha/ekumenme/Ekumenbackend/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
    
    if not os.path.exists(zip_path):
        print(f"❌ ZIP file not found: {zip_path}")
        return False
    
    print(f"📁 Found EPHY ZIP file: {os.path.basename(zip_path)}")
    print(f"📊 File size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
    
    try:
        importer = EPHYImporter()
        
        # Create tables
        await importer.create_tables()
        
        # Import data
        print("\n🚀 Starting EPHY data import...")
        result = await importer.import_from_zip(zip_path)
        
        # Display results
        print("\n" + "=" * 50)
        print("📊 IMPORT SUMMARY")
        print("=" * 50)
        print(f"✅ Products: {result['produits']:,}")
        print(f"✅ Substances: {result['substances']:,}")
        print(f"✅ Titulaires: {result['titulaires']:,}")
        print(f"✅ Usages: {result['usages']:,}")
        print(f"✅ Classifications: {result['classifications']:,}")
        print(f"✅ Conditions: {result['conditions']:,}")
        print(f"✅ Risk phrases: {result['phrases_risque']:,}")
        print(f"✅ Import permits: {result['permis']:,}")
        print(f"❌ Errors: {len(result['errors'])}")
        
        if result['errors']:
            print("\n⚠️  Errors encountered:")
            for error in result['errors'][:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(result['errors']) > 10:
                print(f"   ... and {len(result['errors']) - 10} more errors")
        
        print(f"\n🎉 EPHY import completed!")
        print(f"📈 Total records imported: {sum(v for k, v in result.items() if k != 'errors' and isinstance(v, int)):,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
