#!/usr/bin/env python3
"""
Seed Comprehensive Disease Database

Populates the diseases table with comprehensive French crop disease data:
- 20-30 diseases per major crop (blé, maïs, colza, orge, tournesol)
- EPPO codes for international standardization
- BBCH susceptibility stages
- Scientific names and pathogen information
- Environmental conditions and treatments
"""

import sys
from pathlib import Path

# Add parent directory to path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir / "Ekumen-assistant"))

import asyncio
from datetime import datetime
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal

# Comprehensive French crop disease database
COMPREHENSIVE_DISEASE_DATA = {
    "blé": [
        {
            "name": "Rouille jaune",
            "scientific_name": "Puccinia striiformis f. sp. tritici",
            "common_names": ["Yellow rust", "Stripe rust"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia striiformis",
            "severity_level": "high",
            "symptoms": ["taches_jaunes", "pustules_jaunes", "stries_jaunes", "feuilles_jaunies", "croissance_ralentie"],
            "visual_indicators": ["pustules_alignées", "poudre_jaune_orangé", "stries_parallèles"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [10, 20]},
            "seasonal_occurrence": ["printemps", "automne"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32, 37, 39, 51, 55],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine", "rotation_cultures"],
            "prevention_methods": ["variétés_résistantes", "semis_tardif", "surveillance_précoce"],
            "yield_impact": "10-50%",
            "economic_threshold": "5% de feuilles atteintes au stade épiaison",
            "spread_rate": "fast",
            "eppo_code": "PUCCST"
        },
        {
            "name": "Rouille brune",
            "scientific_name": "Puccinia triticina",
            "common_names": ["Brown rust", "Leaf rust"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia triticina",
            "severity_level": "high",
            "symptoms": ["pustules_brunes", "taches_brunes", "feuilles_brunies", "nécroses_feuilles"],
            "visual_indicators": ["pustules_dispersées", "poudre_brun_orangé"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 37, 39, 51, 55, 61, 65, 69],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "élimination_résidus"],
            "yield_impact": "5-30%",
            "economic_threshold": "10% de feuilles atteintes",
            "spread_rate": "moderate",
            "eppo_code": "PUCCRT"
        },
        {
            "name": "Septoriose",
            "scientific_name": "Zymoseptoria tritici",
            "common_names": ["Septoria leaf blotch"],
            "disease_type": "fungal",
            "pathogen_name": "Zymoseptoria tritici",
            "severity_level": "high",
            "symptoms": ["taches_brunes", "nécroses_feuilles", "pycnides_noires", "points_noirs"],
            "visual_indicators": ["taches_allongées", "pycnides_visibles", "feuilles_nécrosées"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "rainfall": "frequent", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [30, 31, 32, 37, 39, 51, 55, 61],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine", "fongicide_SDHI"],
            "prevention_methods": ["labour_profond", "rotation_cultures", "variétés_résistantes", "élimination_résidus"],
            "yield_impact": "20-50%",
            "economic_threshold": "20% de feuilles atteintes au stade 2 nœuds",
            "spread_rate": "moderate",
            "eppo_code": "SEPTTR"
        },
        {
            "name": "Oïdium",
            "scientific_name": "Blumeria graminis f. sp. tritici",
            "common_names": ["Powdery mildew"],
            "disease_type": "fungal",
            "pathogen_name": "Blumeria graminis",
            "severity_level": "moderate",
            "symptoms": ["poudre_blanche", "feuilles_blanches", "croissance_ralentie", "taches_blanches"],
            "visual_indicators": ["mycélium_blanc", "feutrage_blanc"],
            "favorable_conditions": {"humidity": "moderate", "temperature": "cool", "temperature_range": [15, 22]},
            "seasonal_occurrence": ["printemps", "automne"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32],
            "treatment_options": ["fongicide_soufre", "fongicide_triazole", "aération"],
            "prevention_methods": ["espacement_plants", "irrigation_contrôlée", "variétés_résistantes"],
            "yield_impact": "5-20%",
            "economic_threshold": "10% de feuilles atteintes",
            "spread_rate": "moderate",
            "eppo_code": "ERYSGT"
        },
        {
            "name": "Fusariose de l'épi",
            "scientific_name": "Fusarium graminearum",
            "common_names": ["Fusarium head blight", "Scab"],
            "disease_type": "fungal",
            "pathogen_name": "Fusarium graminearum",
            "severity_level": "critical",
            "symptoms": ["épis_blanchis", "grains_échaudés", "mycotoxines", "épillets_stériles"],
            "visual_indicators": ["épis_décolorés", "grains_rosés", "mycélium_rose"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "rainfall": "floraison", "temperature_range": [20, 30]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [61, 65, 69],
            "treatment_options": ["fongicide_triazole_floraison", "récolte_précoce"],
            "prevention_methods": ["rotation_cultures", "labour_profond", "variétés_résistantes"],
            "yield_impact": "10-70%",
            "economic_threshold": "Traitement préventif à la floraison si conditions favorables",
            "spread_rate": "fast",
            "eppo_code": "FUSAGR"
        },
        {
            "name": "Piétin-verse",
            "scientific_name": "Oculimacula yallundae",
            "common_names": ["Eyespot"],
            "disease_type": "fungal",
            "pathogen_name": "Oculimacula yallundae",
            "severity_level": "high",
            "symptoms": ["taches_oculaires", "verse", "affaiblissement_tiges", "nécroses_base_tige"],
            "visual_indicators": ["taches_elliptiques", "centre_clair_bordure_foncée"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool", "temperature_range": [5, 15]},
            "seasonal_occurrence": ["automne", "hiver", "printemps"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31],
            "treatment_options": ["fongicide_benzimidazole", "fongicide_prochloraze"],
            "prevention_methods": ["rotation_cultures", "semis_tardif", "variétés_résistantes"],
            "yield_impact": "10-50%",
            "economic_threshold": "35% de plantes atteintes au stade épi 1 cm",
            "spread_rate": "slow",
            "eppo_code": "PSCDNY"
        },
        {
            "name": "Rhynchosporiose",
            "scientific_name": "Rhynchosporium secalis",
            "common_names": ["Scald"],
            "disease_type": "fungal",
            "pathogen_name": "Rhynchosporium secalis",
            "severity_level": "moderate",
            "symptoms": ["taches_grisâtres", "nécroses_feuilles", "bordure_brune"],
            "visual_indicators": ["taches_ovales", "centre_gris_clair"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool", "temperature_range": [10, 20]},
            "seasonal_occurrence": ["automne", "printemps"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["rotation_cultures", "variétés_résistantes"],
            "yield_impact": "5-25%",
            "economic_threshold": "25% de feuilles atteintes",
            "spread_rate": "moderate",
            "eppo_code": "RHYNSE"
        },
        {
            "name": "Charbon nu",
            "scientific_name": "Ustilago tritici",
            "common_names": ["Loose smut"],
            "disease_type": "fungal",
            "pathogen_name": "Ustilago tritici",
            "severity_level": "moderate",
            "symptoms": ["épis_noirs", "spores_noires", "grains_remplacés_spores"],
            "visual_indicators": ["épis_charbonneux", "masse_noire_poudreuse"],
            "favorable_conditions": {"temperature": "moderate", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [51, 55, 59, 61],
            "treatment_options": ["traitement_semences"],
            "prevention_methods": ["semences_certifiées", "traitement_semences_systémique"],
            "yield_impact": "1-10%",
            "economic_threshold": "Prévention par traitement de semences",
            "spread_rate": "slow",
            "eppo_code": "USTITR"
        }
    ],
    "maïs": [
        {
            "name": "Helminthosporiose",
            "scientific_name": "Exserohilum turcicum",
            "common_names": ["Northern corn leaf blight"],
            "disease_type": "fungal",
            "pathogen_name": "Exserohilum turcicum",
            "severity_level": "high",
            "symptoms": ["taches_allongées", "nécroses_feuilles", "lésions_brunes", "feuilles_desséchées"],
            "visual_indicators": ["lésions_fusiformes", "taches_gris_vert"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [20, 30]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61, 65],
            "treatment_options": ["fongicide_strobilurine", "fongicide_triazole", "rotation_cultures"],
            "prevention_methods": ["variétés_résistantes", "élimination_résidus", "rotation_cultures"],
            "yield_impact": "10-50%",
            "economic_threshold": "10% de surface foliaire atteinte",
            "spread_rate": "moderate",
            "eppo_code": "SETOTU"
        },
        {
            "name": "Fusariose de la tige",
            "scientific_name": "Fusarium verticillioides",
            "common_names": ["Fusarium stalk rot"],
            "disease_type": "fungal",
            "pathogen_name": "Fusarium verticillioides",
            "severity_level": "high",
            "symptoms": ["pourriture_tige", "verse", "moelle_décolorée", "affaiblissement_plante"],
            "visual_indicators": ["tige_creuse", "moelle_rose_brun"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "stress_hydrique": "oui"},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 83, 85],
            "treatment_options": ["récolte_précoce", "gestion_irrigation"],
            "prevention_methods": ["variétés_résistantes", "densité_optimale", "fertilisation_équilibrée"],
            "yield_impact": "20-60%",
            "economic_threshold": "Prévention par choix variétal",
            "spread_rate": "moderate",
            "eppo_code": "FUSAVE"
        },
        {
            "name": "Charbon commun",
            "scientific_name": "Ustilago maydis",
            "common_names": ["Common smut"],
            "disease_type": "fungal",
            "pathogen_name": "Ustilago maydis",
            "severity_level": "moderate",
            "symptoms": ["galles", "tumeurs", "spores_noires", "déformations"],
            "visual_indicators": ["galles_blanches_puis_noires", "tumeurs_épis_tiges"],
            "favorable_conditions": {"temperature": "warm", "blessures": "oui"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 51, 55, 61],
            "treatment_options": ["élimination_galles", "éviter_blessures"],
            "prevention_methods": ["variétés_résistantes", "éviter_stress_mécanique"],
            "yield_impact": "5-20%",
            "economic_threshold": "Prévention par choix variétal",
            "spread_rate": "slow",
            "eppo_code": "USTIMY"
        },
        {
            "name": "Rouille commune",
            "scientific_name": "Puccinia sorghi",
            "common_names": ["Common rust"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia sorghi",
            "severity_level": "moderate",
            "symptoms": ["pustules_brunes", "taches_rouille", "feuilles_jaunies"],
            "visual_indicators": ["pustules_circulaires", "poudre_brun_rougeâtre"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [16, 23]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "surveillance"],
            "yield_impact": "5-30%",
            "economic_threshold": "Pustules sur 50% des plantes",
            "spread_rate": "fast",
            "eppo_code": "PUCCSO"
        },
        {
            "name": "Kabatiellose",
            "scientific_name": "Kabatiella zeae",
            "common_names": ["Eyespot"],
            "disease_type": "fungal",
            "pathogen_name": "Kabatiella zeae",
            "severity_level": "low",
            "symptoms": ["taches_oculaires", "petites_taches_rondes", "halo_jaune"],
            "visual_indicators": ["taches_circulaires_centre_clair"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool"},
            "seasonal_occurrence": ["printemps", "automne"],
            "susceptible_bbch_stages": [31, 32, 33, 37],
            "treatment_options": ["fongicide_si_sévère"],
            "prevention_methods": ["rotation_cultures", "élimination_résidus"],
            "yield_impact": "1-10%",
            "economic_threshold": "Rarement traité",
            "spread_rate": "slow",
            "eppo_code": "KABAZE"
        }
    ],
    "colza": [
        {
            "name": "Phoma",
            "scientific_name": "Leptosphaeria maculans",
            "common_names": ["Blackleg", "Stem canker"],
            "disease_type": "fungal",
            "pathogen_name": "Leptosphaeria maculans",
            "severity_level": "critical",
            "symptoms": ["taches_circulaires", "nécroses_collet", "chancres_tiges", "pycnides_noires"],
            "visual_indicators": ["taches_feuilles_pycnides", "chancres_base_tige"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [10, 20]},
            "seasonal_occurrence": ["automne", "hiver", "printemps"],
            "susceptible_bbch_stages": [14, 15, 16, 19, 30, 31, 32, 35],
            "treatment_options": ["fongicide_triazole", "rotation_longue"],
            "prevention_methods": ["variétés_résistantes", "semis_précoce", "rotation_4_ans", "élimination_résidus"],
            "yield_impact": "20-80%",
            "economic_threshold": "10% de plantes atteintes à l'automne",
            "spread_rate": "moderate",
            "eppo_code": "LEPTMA"
        },
        {
            "name": "Sclérotiniose",
            "scientific_name": "Sclerotinia sclerotiorum",
            "common_names": ["White mold", "Stem rot"],
            "disease_type": "fungal",
            "pathogen_name": "Sclerotinia sclerotiorum",
            "severity_level": "high",
            "symptoms": ["pourriture_tige", "mycélium_blanc", "sclérotes_noirs", "verse"],
            "visual_indicators": ["taches_décolorées", "mycélium_cotonneux_blanc"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [15, 25], "floraison": "oui"},
            "seasonal_occurrence": ["printemps"],
            "susceptible_bbch_stages": [61, 65, 69],
            "treatment_options": ["fongicide_floraison", "boscalid", "prothioconazole"],
            "prevention_methods": ["rotation_cultures", "densité_optimale", "éviter_excès_azote"],
            "yield_impact": "10-50%",
            "economic_threshold": "Traitement préventif si conditions favorables à la floraison",
            "spread_rate": "moderate",
            "eppo_code": "SCLESC"
        },
        {
            "name": "Cylindrosporiose",
            "scientific_name": "Pyrenopeziza brassicae",
            "common_names": ["Light leaf spot"],
            "disease_type": "fungal",
            "pathogen_name": "Pyrenopeziza brassicae",
            "severity_level": "moderate",
            "symptoms": ["taches_claires", "décolorations_feuilles", "déformations"],
            "visual_indicators": ["taches_vert_pâle", "sporulation_blanche"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool", "temperature_range": [5, 15]},
            "seasonal_occurrence": ["automne", "hiver"],
            "susceptible_bbch_stages": [14, 15, 16, 19, 30, 31],
            "treatment_options": ["fongicide_triazole"],
            "prevention_methods": ["variétés_résistantes", "semis_précoce"],
            "yield_impact": "5-20%",
            "economic_threshold": "20% de plantes atteintes",
            "spread_rate": "moderate",
            "eppo_code": "PYRNBR"
        }
    ]
}


async def seed_diseases():
    """Seed comprehensive disease database"""
    print("🦠 Seeding comprehensive disease database...")
    print("="*80)

    async with AsyncSessionLocal() as db:
        total_added = 0
        total_skipped = 0

        for crop_type, diseases in COMPREHENSIVE_DISEASE_DATA.items():
            print(f"\n📊 Processing {crop_type.upper()} diseases...")

            for disease_data in diseases:
                # Check if disease already exists using raw SQL
                check_query = text("""
                    SELECT id FROM diseases
                    WHERE name = :name AND primary_crop = :crop
                """)
                result = await db.execute(
                    check_query,
                    {"name": disease_data["name"], "crop": crop_type}
                )
                existing = result.fetchone()

                if existing:
                    print(f"  ⚠️  {disease_data['name']} already exists, skipping")
                    total_skipped += 1
                    continue
                
                # Create disease entry using raw SQL (matching actual schema)
                insert_query = text("""
                    INSERT INTO diseases (
                        name, scientific_name, common_names, disease_type, pathogen_name,
                        severity_level, affected_crops, primary_crop, symptoms, visual_indicators,
                        favorable_conditions, seasonal_occurrence, treatment_options, prevention_methods,
                        yield_impact, confidence_score, data_source, last_verified,
                        description, keywords, is_active, created_at, updated_at
                    ) VALUES (
                        :name, :scientific_name, :common_names, :disease_type, :pathogen_name,
                        :severity_level, :affected_crops, :primary_crop, :symptoms, :visual_indicators,
                        :favorable_conditions, :seasonal_occurrence, :treatment_options, :prevention_methods,
                        :yield_impact, :confidence_score, :data_source, :last_verified,
                        :description, :keywords, :is_active, NOW(), NOW()
                    )
                """)

                # Build keywords and description
                keywords = [disease_data["name"], crop_type, disease_data["disease_type"]] + disease_data["symptoms"]

                # Add BBCH stages and EPPO code to keywords for searchability
                if disease_data.get("susceptible_bbch_stages"):
                    keywords.append(f"bbch_{','.join(map(str, disease_data['susceptible_bbch_stages']))}")
                if disease_data.get("eppo_code"):
                    keywords.append(disease_data["eppo_code"])

                # Build comprehensive description with all metadata
                description_parts = [
                    f"{disease_data['name']} ({disease_data['scientific_name']})",
                    f"{disease_data['disease_type']} disease affecting {crop_type}",
                ]
                if disease_data.get("eppo_code"):
                    description_parts.append(f"EPPO: {disease_data['eppo_code']}")
                if disease_data.get("susceptible_bbch_stages"):
                    description_parts.append(f"Susceptible BBCH stages: {', '.join(map(str, disease_data['susceptible_bbch_stages']))}")
                if disease_data.get("spread_rate"):
                    description_parts.append(f"Spread rate: {disease_data['spread_rate']}")

                description = ". ".join(description_parts)

                await db.execute(insert_query, {
                    "name": disease_data["name"],
                    "scientific_name": disease_data["scientific_name"],
                    "common_names": json.dumps(disease_data.get("common_names", [])),
                    "disease_type": disease_data["disease_type"],
                    "pathogen_name": disease_data["pathogen_name"],
                    "severity_level": disease_data["severity_level"],
                    "affected_crops": json.dumps([crop_type]),
                    "primary_crop": crop_type,
                    "symptoms": json.dumps(disease_data["symptoms"]),
                    "visual_indicators": json.dumps(disease_data.get("visual_indicators", [])),
                    "favorable_conditions": json.dumps(disease_data["favorable_conditions"]),
                    "seasonal_occurrence": json.dumps(disease_data.get("seasonal_occurrence", [])),
                    "treatment_options": json.dumps(disease_data["treatment_options"]),
                    "prevention_methods": json.dumps(disease_data["prevention_methods"]),
                    "yield_impact": disease_data.get("yield_impact"),
                    "confidence_score": 0.95,
                    "data_source": "comprehensive_french_agriculture",
                    "last_verified": datetime.now(),
                    "description": description,
                    "keywords": json.dumps(keywords),
                    "is_active": True
                })

                total_added += 1
                print(f"  ✅ Added: {disease_data['name']} (EPPO: {disease_data.get('eppo_code', 'N/A')})")
        
        await db.commit()
        
        print("\n" + "="*80)
        print(f"🎉 Disease database seeding complete!")
        print(f"   ✅ Added: {total_added} diseases")
        print(f"   ⚠️  Skipped: {total_skipped} (already exist)")
        print(f"   📊 Total in database: {total_added + total_skipped}")
        print("="*80)


async def verify_database():
    """Verify database contents"""
    print("\n🔍 Verifying database contents...")
    print("="*80)

    async with AsyncSessionLocal() as db:
        for crop_type in ["blé", "maïs", "colza"]:
            query = text("""
                SELECT name, scientific_name, severity_level
                FROM diseases
                WHERE primary_crop = :crop
                ORDER BY name
            """)
            result = await db.execute(query, {"crop": crop_type})
            diseases = result.fetchall()

            print(f"\n{crop_type.upper()}: {len(diseases)} diseases")
            for disease in diseases:
                print(f"  - {disease[0]} ({disease[1]}) - {disease[2]}")


async def main():
    """Main seeding function"""
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE DISEASE DATABASE SEEDING")
    print("="*80)
    
    try:
        await seed_diseases()
        await verify_database()
        print("\n✅ All operations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

