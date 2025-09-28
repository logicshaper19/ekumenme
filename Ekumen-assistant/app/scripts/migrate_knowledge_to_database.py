#!/usr/bin/env python3
"""
Migrate Legacy Knowledge to Database

This script migrates hardcoded disease and pest knowledge from tools
to the new database tables for semantic search and better management.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.disease import Disease
from app.models.pest import Pest

# Legacy disease knowledge from DiagnoseDiseaseTool
LEGACY_DISEASE_KNOWLEDGE = {
    "blé": {
        "rouille_jaune": {
            "symptoms": ["taches_jaunes", "pustules_jaunes", "feuilles_jaunies"],
            "conditions": {"humidity": "high", "temperature": "moderate"},
            "severity": "moderate",
            "treatment": ["fongicide_triazole", "rotation_cultures"],
            "prevention": ["variétés_résistantes", "drainage_amélioré"]
        },
        "oïdium": {
            "symptoms": ["poudre_blanche", "feuilles_blanches", "croissance_ralentie"],
            "conditions": {"humidity": "high", "temperature": "cool"},
            "severity": "moderate",
            "treatment": ["fongicide_soufre", "aération"],
            "prevention": ["espacement_plants", "irrigation_contrôlée"]
        },
        "septoriose": {
            "symptoms": ["taches_brunes", "feuilles_brunies", "chute_feuilles"],
            "conditions": {"humidity": "very_high", "temperature": "moderate"},
            "severity": "high",
            "treatment": ["fongicide_systémique", "défoliation"],
            "prevention": ["rotation_cultures", "drainage"]
        }
    },
    "maïs": {
        "helminthosporiose": {
            "symptoms": ["taches_brunes", "feuilles_brunies", "croissance_ralentie"],
            "conditions": {"humidity": "high", "temperature": "warm"},
            "severity": "moderate",
            "treatment": ["fongicide_contact", "rotation_cultures"],
            "prevention": ["variétés_résistantes", "drainage"]
        },
        "charbon": {
            "symptoms": ["excroissances_noires", "grains_noirs", "croissance_anormale"],
            "conditions": {"humidity": "high", "temperature": "warm"},
            "severity": "high",
            "treatment": ["fongicide_systémique", "destruction_plants"],
            "prevention": ["traitement_semences", "rotation_cultures"]
        }
    },
    "colza": {
        "sclérotinia": {
            "symptoms": ["taches_blanches", "pourriture_tige", "croissance_ralentie"],
            "conditions": {"humidity": "very_high", "temperature": "cool"},
            "severity": "high",
            "treatment": ["fongicide_préventif", "rotation_cultures"],
            "prevention": ["espacement_plants", "drainage"]
        }
    }
}

# Legacy pest knowledge from IdentifyPestTool
LEGACY_PEST_KNOWLEDGE = {
    "blé": {
        "puceron": {
            "damage_patterns": ["feuilles_jaunies", "croissance_ralentie", "miellat"],
            "pest_indicators": ["pucerons_verts", "pucerons_noirs", "fourmis"],
            "severity": "moderate",
            "treatment": ["insecticide_systémique", "coccinelles"],
            "prevention": ["variétés_résistantes", "rotation_cultures"]
        },
        "cécidomyie": {
            "damage_patterns": ["épis_vides", "grains_abîmés", "croissance_anormale"],
            "pest_indicators": ["larves_blanches", "mouches_jaunes"],
            "severity": "high",
            "treatment": ["insecticide_contact", "pièges_phéromones"],
            "prevention": ["traitement_semences", "rotation_cultures"]
        },
        "limace": {
            "damage_patterns": ["feuilles_rongées", "trous_irréguliers", "traces_visqueuses"],
            "pest_indicators": ["limaces", "traces_argentées"],
            "severity": "moderate",
            "treatment": ["anti-limaces", "pièges_bière"],
            "prevention": ["drainage", "paillage"]
        }
    },
    "maïs": {
        "pyrale": {
            "damage_patterns": ["trous_tiges", "épis_abîmés", "croissance_ralentie"],
            "pest_indicators": ["chenilles", "papillons_bruns"],
            "severity": "high",
            "treatment": ["insecticide_systémique", "trichogrammes"],
            "prevention": ["variétés_bt", "rotation_cultures"]
        },
        "taupin": {
            "damage_patterns": ["racines_rongées", "plants_flétris", "croissance_ralentie"],
            "pest_indicators": ["larves_jaunes", "adultes_noirs"],
            "severity": "moderate",
            "treatment": ["insecticide_sol", "nématodes"],
            "prevention": ["traitement_semences", "rotation_cultures"]
        }
    },
    "colza": {
        "altise": {
            "damage_patterns": ["trous_feuilles", "feuilles_criblées", "croissance_ralentie"],
            "pest_indicators": ["petits_coléoptères", "sautillements"],
            "severity": "moderate",
            "treatment": ["insecticide_contact", "pièges_jaunes"],
            "prevention": ["semis_précoce", "rotation_cultures"]
        }
    }
}

async def migrate_diseases_to_database():
    """Migrate legacy disease knowledge to database."""
    print("🦠 Migrating disease knowledge to database...")
    
    async with AsyncSessionLocal() as db:
        disease_count = 0
        
        for crop_type, diseases in LEGACY_DISEASE_KNOWLEDGE.items():
            for disease_name, disease_data in diseases.items():
                
                # Check if disease already exists
                existing = await db.execute(
                    "SELECT id FROM diseases WHERE name = :name AND primary_crop = :crop",
                    {"name": disease_name, "crop": crop_type}
                )
                if existing.fetchone():
                    print(f"  ⚠️ Disease {disease_name} for {crop_type} already exists, skipping")
                    continue
                
                # Create disease from legacy data
                disease = Disease.from_legacy_data(disease_name, crop_type, disease_data)
                
                # Add enhanced metadata
                disease.disease_type = "fungal"  # Most crop diseases are fungal
                disease.scientific_name = f"{disease_name.title()} sp."
                disease.common_names = [disease_name.replace("_", " ").title()]
                disease.description = f"Maladie fongique affectant {crop_type}: {disease_name.replace('_', ' ')}"
                
                # Enhanced keywords for search
                disease.keywords = [
                    disease_name, crop_type, disease.disease_type
                ] + disease.symptoms + disease.treatment_options
                
                db.add(disease)
                disease_count += 1
                print(f"  ✅ Added disease: {disease_name} for {crop_type}")
        
        await db.commit()
        print(f"🎉 Successfully migrated {disease_count} diseases to database!")

async def migrate_pests_to_database():
    """Migrate legacy pest knowledge to database."""
    print("🐛 Migrating pest knowledge to database...")
    
    async with AsyncSessionLocal() as db:
        pest_count = 0
        
        for crop_type, pests in LEGACY_PEST_KNOWLEDGE.items():
            for pest_name, pest_data in pests.items():
                
                # Check if pest already exists
                existing = await db.execute(
                    "SELECT id FROM pests WHERE name = :name AND primary_crop = :crop",
                    {"name": pest_name, "crop": crop_type}
                )
                if existing.fetchone():
                    print(f"  ⚠️ Pest {pest_name} for {crop_type} already exists, skipping")
                    continue
                
                # Create pest from legacy data
                pest = Pest.from_legacy_data(pest_name, crop_type, pest_data)
                
                # Add enhanced metadata
                pest.pest_type = "insect"  # Most crop pests are insects
                pest.scientific_name = f"{pest_name.title()} sp."
                pest.common_names = [pest_name.replace("_", " ").title()]
                pest.description = f"Ravageur affectant {crop_type}: {pest_name.replace('_', ' ')}"
                
                # Enhanced keywords for search
                pest.keywords = [
                    pest_name, crop_type, pest.pest_type
                ] + pest.damage_patterns + pest.pest_indicators
                
                db.add(pest)
                pest_count += 1
                print(f"  ✅ Added pest: {pest_name} for {crop_type}")
        
        await db.commit()
        print(f"🎉 Successfully migrated {pest_count} pests to database!")

async def main():
    """Main migration function."""
    print("🚀 Starting knowledge migration to database...")
    
    try:
        await migrate_diseases_to_database()
        await migrate_pests_to_database()
        print("\n✅ Knowledge migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
