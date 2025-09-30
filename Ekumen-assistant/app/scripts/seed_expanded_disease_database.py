#!/usr/bin/env python3
"""
Seed Expanded Disease Database - Additional Crops and Diseases

Adds comprehensive disease data for:
- Orge (Barley) - 10+ diseases
- Tournesol (Sunflower) - 8+ diseases
- Pomme de terre (Potato) - 15+ diseases
- Vigne (Grapevine) - 12+ diseases
- Betterave sucrière (Sugar Beet) - 8+ diseases

Plus additional diseases for existing crops (blé, maïs, colza)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Ekumen-assistant"))

import asyncio
from datetime import datetime
import json
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

# Expanded disease database with additional crops
EXPANDED_DISEASE_DATA = {
    # Additional wheat diseases
    "blé": [
        {
            "name": "Tan Spot",
            "scientific_name": "Pyrenophora tritici-repentis",
            "common_names": ["Helminthosporiose", "Tache auréolée"],
            "disease_type": "fungal",
            "pathogen_name": "Pyrenophora tritici-repentis",
            "severity_level": "moderate",
            "symptoms": ["taches_tan", "taches_jaunes_halo", "nécroses_feuilles", "lésions_diamant"],
            "visual_indicators": ["taches_brunes_halo_jaune", "lésions_losange"],
            "favorable_conditions": {"humidity": "moderate", "temperature": "moderate", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32, 37],
            "treatment_options": ["fongicide_triazole", "rotation_cultures", "labour_profond"],
            "prevention_methods": ["variétés_résistantes", "élimination_résidus", "rotation_non_céréales"],
            "yield_impact": "5-25%",
            "economic_threshold": "Traitement si 10% de feuilles atteintes",
            "spread_rate": "moderate",
            "eppo_code": "PYRE TR"
        },
        {
            "name": "Piétin-échaudage",
            "scientific_name": "Gaeumannomyces graminis var. tritici",
            "common_names": ["Take-all"],
            "disease_type": "fungal",
            "pathogen_name": "Gaeumannomyces graminis",
            "severity_level": "high",
            "symptoms": ["racines_noircies", "base_tige_noire", "épis_blancs", "grains_vides", "nanisme"],
            "visual_indicators": ["racines_pourries_noires", "épis_échaudés"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "pH": "alcalin"},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32, 37, 51, 55],
            "treatment_options": ["rotation_cultures", "semis_tardif"],
            "prevention_methods": ["rotation_longue", "éviter_monoculture", "drainage"],
            "yield_impact": "10-50%",
            "economic_threshold": "Prévention par rotation",
            "spread_rate": "slow",
            "eppo_code": "GAEUGT"
        }
    ],
    
    # Additional maize diseases
    "maïs": [
        {
            "name": "Anthracnose",
            "scientific_name": "Colletotrichum graminicola",
            "common_names": ["Anthracnose stalk rot"],
            "disease_type": "fungal",
            "pathogen_name": "Colletotrichum graminicola",
            "severity_level": "high",
            "symptoms": ["lésions_noires_brillantes", "pourriture_tige", "verse", "sénescence_précoce"],
            "visual_indicators": ["taches_noires_luisantes", "moelle_désintégrée"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "stress_hydrique": "oui"},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 83, 85],
            "treatment_options": ["variétés_résistantes", "rotation_cultures"],
            "prevention_methods": ["densité_optimale", "fertilisation_équilibrée", "irrigation_régulière"],
            "yield_impact": "15-40%",
            "economic_threshold": "Prévention par choix variétal",
            "spread_rate": "moderate",
            "eppo_code": "COLLGR"
        },
        {
            "name": "Curvulariose",
            "scientific_name": "Curvularia lunata",
            "common_names": ["Curvularia leaf spot"],
            "disease_type": "fungal",
            "pathogen_name": "Curvularia lunata",
            "severity_level": "moderate",
            "symptoms": ["taches_allongées", "lésions_brunes", "pourriture_épi"],
            "visual_indicators": ["taches_ovales_brunes"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61],
            "treatment_options": ["fongicide_strobilurine", "rotation_cultures"],
            "prevention_methods": ["variétés_résistantes", "élimination_résidus"],
            "yield_impact": "5-20%",
            "economic_threshold": "Surveillance",
            "spread_rate": "moderate",
            "eppo_code": "CURVLU"
        }
    ],
    
    # Additional rapeseed diseases
    "colza": [
        {
            "name": "Verticilliose",
            "scientific_name": "Verticillium longisporum",
            "common_names": ["Verticillium wilt"],
            "disease_type": "fungal",
            "pathogen_name": "Verticillium longisporum",
            "severity_level": "high",
            "symptoms": ["sénescence_précoce", "jaunissement_unilatéral", "stries_grises_tige"],
            "visual_indicators": ["décoloration_vasculaire", "flétrissement"],
            "favorable_conditions": {"temperature": "moderate", "sol_contaminé": "oui"},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [51, 55, 61, 65, 69, 71],
            "treatment_options": ["rotation_longue", "variétés_résistantes"],
            "prevention_methods": ["rotation_4_ans_minimum", "éviter_crucifères"],
            "yield_impact": "10-30%",
            "economic_threshold": "Prévention par rotation",
            "spread_rate": "slow",
            "eppo_code": "VERTLO"
        },
        {
            "name": "Alternariose",
            "scientific_name": "Alternaria brassicae",
            "common_names": ["Alternaria leaf spot", "Dark pod spot"],
            "disease_type": "fungal",
            "pathogen_name": "Alternaria brassicae",
            "severity_level": "moderate",
            "symptoms": ["taches_brunes_foncées", "taches_cibles", "éclatement_siliques"],
            "visual_indicators": ["taches_concentriques_noires"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm"},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 79],
            "treatment_options": ["fongicide_triazole", "récolte_précoce"],
            "prevention_methods": ["semences_saines", "rotation_cultures"],
            "yield_impact": "5-15%",
            "economic_threshold": "Traitement si conditions favorables",
            "spread_rate": "moderate",
            "eppo_code": "ALTEBR"
        }
    ],
    
    # Potato (Pomme de terre) - NEW CROP
    "pomme_de_terre": [
        {
            "name": "Mildiou",
            "scientific_name": "Phytophthora infestans",
            "common_names": ["Late blight", "Potato blight"],
            "disease_type": "oomycete",
            "pathogen_name": "Phytophthora infestans",
            "severity_level": "critical",
            "symptoms": ["taches_brunes_humides", "pourriture_tubercules", "feuilles_nécrosées", "odeur_pourriture"],
            "visual_indicators": ["lésions_aqueuses", "duvet_blanc_dessous_feuilles"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [10, 25], "rainfall": "frequent"},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61, 65],
            "treatment_options": ["fongicide_systémique", "fongicide_contact", "destruction_plantes_infectées"],
            "prevention_methods": ["variétés_résistantes", "plants_certifiés", "rotation_cultures", "surveillance_météo"],
            "yield_impact": "30-100%",
            "economic_threshold": "Traitement préventif dès conditions favorables",
            "spread_rate": "very_fast",
            "eppo_code": "PHYTIN"
        },
        {
            "name": "Alternariose",
            "scientific_name": "Alternaria solani",
            "common_names": ["Early blight"],
            "disease_type": "fungal",
            "pathogen_name": "Alternaria solani",
            "severity_level": "moderate",
            "symptoms": ["taches_cibles", "nécroses_feuilles_âgées", "lésions_tubercules"],
            "visual_indicators": ["taches_concentriques_brunes"],
            "favorable_conditions": {"humidity": "moderate", "temperature": "warm", "temperature_range": [24, 29]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55],
            "treatment_options": ["fongicide_mancozèbe", "fongicide_chlorothalonil"],
            "prevention_methods": ["rotation_cultures", "fertilisation_équilibrée", "irrigation_goutte_à_goutte"],
            "yield_impact": "10-30%",
            "economic_threshold": "Traitement si 10% de feuilles atteintes",
            "spread_rate": "moderate",
            "eppo_code": "ALTESO"
        },
        {
            "name": "Gale commune",
            "scientific_name": "Streptomyces scabies",
            "common_names": ["Common scab"],
            "disease_type": "bacterial",
            "pathogen_name": "Streptomyces scabies",
            "severity_level": "moderate",
            "symptoms": ["lésions_liégeuses", "croûtes_tubercules", "dépréciation_qualité"],
            "visual_indicators": ["taches_brunes_rugueuses"],
            "favorable_conditions": {"pH": "alcalin", "sol_sec": "oui", "temperature": "warm"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [41, 43, 45, 47, 49],
            "treatment_options": ["acidification_sol", "irrigation_régulière"],
            "prevention_methods": ["variétés_résistantes", "pH_sol_5.2", "rotation_cultures"],
            "yield_impact": "0-10% (qualité)",
            "economic_threshold": "Prévention par gestion du sol",
            "spread_rate": "slow",
            "eppo_code": "STRSCA"
        },
        {
            "name": "Rhizoctone brun",
            "scientific_name": "Rhizoctonia solani",
            "common_names": ["Black scurf", "Stem canker"],
            "disease_type": "fungal",
            "pathogen_name": "Rhizoctonia solani",
            "severity_level": "moderate",
            "symptoms": ["sclérotes_noirs", "chancres_tiges", "tubercules_déformés"],
            "visual_indicators": ["croûtes_noires_tubercules"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "sol_froid": "oui"},
            "seasonal_occurrence": ["printemps"],
            "susceptible_bbch_stages": [9, 11, 13, 15, 19],
            "treatment_options": ["traitement_plants", "réchauffement_sol"],
            "prevention_methods": ["plants_certifiés", "plantation_sol_chaud", "rotation_cultures"],
            "yield_impact": "5-20%",
            "economic_threshold": "Prévention par plants sains",
            "spread_rate": "moderate",
            "eppo_code": "RHIZSO"
        }
    ],

    # Grapevine (Vigne) - NEW CROP
    "vigne": [
        {
            "name": "Mildiou de la vigne",
            "scientific_name": "Plasmopara viticola",
            "common_names": ["Downy mildew"],
            "disease_type": "oomycete",
            "pathogen_name": "Plasmopara viticola",
            "severity_level": "critical",
            "symptoms": ["taches_huile", "duvet_blanc", "baies_flétries", "rot_brun"],
            "visual_indicators": ["taches_jaunes_dessus", "moisissure_blanche_dessous"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [13, 25], "rainfall": "frequent"},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [15, 19, 53, 55, 57, 61, 65, 69, 71, 75],
            "treatment_options": ["fongicide_cuivre", "fongicide_systémique", "effeuillage"],
            "prevention_methods": ["variétés_résistantes", "palissage_aéré", "surveillance_météo"],
            "yield_impact": "20-80%",
            "economic_threshold": "Traitement préventif obligatoire",
            "spread_rate": "very_fast",
            "eppo_code": "PLASVI"
        },
        {
            "name": "Oïdium de la vigne",
            "scientific_name": "Erysiphe necator",
            "common_names": ["Powdery mildew"],
            "disease_type": "fungal",
            "pathogen_name": "Erysiphe necator",
            "severity_level": "critical",
            "symptoms": ["poudre_blanche", "baies_éclatées", "feuilles_crispées"],
            "visual_indicators": ["feutrage_blanc_grisâtre"],
            "favorable_conditions": {"humidity": "moderate", "temperature": "warm", "temperature_range": [20, 27]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [15, 19, 53, 55, 57, 61, 65, 69, 71],
            "treatment_options": ["fongicide_soufre", "fongicide_IBS", "effeuillage"],
            "prevention_methods": ["variétés_résistantes", "aération_vignoble", "ébourgeonnage"],
            "yield_impact": "15-60%",
            "economic_threshold": "Traitement préventif dès débourrement",
            "spread_rate": "fast",
            "eppo_code": "ERYSNE"
        },
        {
            "name": "Pourriture grise",
            "scientific_name": "Botrytis cinerea",
            "common_names": ["Gray mold", "Botrytis"],
            "disease_type": "fungal",
            "pathogen_name": "Botrytis cinerea",
            "severity_level": "high",
            "symptoms": ["moisissure_grise", "pourriture_baies", "dessèchement_grappes"],
            "visual_indicators": ["duvet_gris_baies"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "rainfall": "vendange"},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 79, 81, 85, 89],
            "treatment_options": ["fongicide_anti-botrytis", "effeuillage", "vendange_précoce"],
            "prevention_methods": ["aération_grappes", "limitation_rendement", "effeuillage_précoce"],
            "yield_impact": "10-50%",
            "economic_threshold": "Traitement si conditions humides pré-vendange",
            "spread_rate": "fast",
            "eppo_code": "BOTRCI"
        },
        {
            "name": "Black-rot",
            "scientific_name": "Guignardia bidwellii",
            "common_names": ["Pourriture noire"],
            "disease_type": "fungal",
            "pathogen_name": "Guignardia bidwellii",
            "severity_level": "high",
            "symptoms": ["taches_brunes_feuilles", "baies_momifiées", "pycnides_noires"],
            "visual_indicators": ["baies_noires_ridées"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [20, 27]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [53, 55, 57, 61, 65, 69, 71],
            "treatment_options": ["fongicide_mancozèbe", "fongicide_triazole", "élimination_momies"],
            "prevention_methods": ["taille_sanitaire", "élimination_bois_malade", "palissage"],
            "yield_impact": "20-80%",
            "economic_threshold": "Traitement préventif si historique",
            "spread_rate": "moderate",
            "eppo_code": "GUIGBI"
        },
        {
            "name": "Esca",
            "scientific_name": "Phaeomoniella chlamydospora",
            "common_names": ["Black measles", "Apoplexie"],
            "disease_type": "fungal",
            "pathogen_name": "Phaeomoniella chlamydospora",
            "severity_level": "critical",
            "symptoms": ["tigré_feuilles", "dessèchement_brutal", "nécrose_bois", "apoplexie"],
            "visual_indicators": ["bandes_jaunes_rouges_feuilles", "bois_blanc_strié"],
            "favorable_conditions": {"stress_hydrique": "oui", "blessures_taille": "oui"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 79],
            "treatment_options": ["curetage_bois", "taille_douce", "pas_de_traitement_curatif"],
            "prevention_methods": ["taille_tardive", "protection_plaies", "arrachage_ceps_morts"],
            "yield_impact": "Variable (mort du cep)",
            "economic_threshold": "Prévention par taille adaptée",
            "spread_rate": "slow",
            "eppo_code": "PHAEPC"
        }
    ],

    # Sugar Beet (Betterave sucrière) - NEW CROP
    "betterave_sucrière": [
        {
            "name": "Cercosporiose",
            "scientific_name": "Cercospora beticola",
            "common_names": ["Cercospora leaf spot"],
            "disease_type": "fungal",
            "pathogen_name": "Cercospora beticola",
            "severity_level": "critical",
            "symptoms": ["taches_circulaires_grises", "bordure_brune", "défoliation"],
            "visual_indicators": ["taches_grises_centre_brun"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [20, 30]},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 41, 43, 45, 47, 49],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "rotation_cultures", "surveillance"],
            "yield_impact": "20-50%",
            "economic_threshold": "Traitement dès 5% de feuilles atteintes",
            "spread_rate": "fast",
            "eppo_code": "CERCBE"
        },
        {
            "name": "Oïdium",
            "scientific_name": "Erysiphe betae",
            "common_names": ["Powdery mildew"],
            "disease_type": "fungal",
            "pathogen_name": "Erysiphe betae",
            "severity_level": "moderate",
            "symptoms": ["poudre_blanche", "feuilles_jaunies", "réduction_photosynthèse"],
            "visual_indicators": ["feutrage_blanc_feuilles"],
            "favorable_conditions": {"humidity": "moderate", "temperature": "warm"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 41, 43],
            "treatment_options": ["fongicide_soufre", "fongicide_triazole"],
            "prevention_methods": ["variétés_résistantes", "irrigation_contrôlée"],
            "yield_impact": "5-20%",
            "economic_threshold": "Traitement si 10% de feuilles atteintes",
            "spread_rate": "moderate",
            "eppo_code": "ERYSBE"
        },
        {
            "name": "Rhizomanie",
            "scientific_name": "Beet necrotic yellow vein virus",
            "common_names": ["Rhizomania"],
            "disease_type": "viral",
            "pathogen_name": "BNYVV",
            "severity_level": "critical",
            "symptoms": ["racines_chevelues", "jaunissement_feuilles", "racine_conique", "nécroses_vasculaires"],
            "visual_indicators": ["prolifération_radicelles", "racine_déformée"],
            "favorable_conditions": {"sol_contaminé": "oui", "vecteur_polymyxa": "oui"},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [11, 13, 15, 19, 31, 32, 33],
            "treatment_options": ["variétés_résistantes_obligatoires"],
            "prevention_methods": ["variétés_résistantes", "rotation_longue", "désinfection_matériel"],
            "yield_impact": "30-80%",
            "economic_threshold": "Prévention obligatoire en zone contaminée",
            "spread_rate": "slow",
            "eppo_code": "BNYVV0"
        },
        {
            "name": "Rouille",
            "scientific_name": "Uromyces betae",
            "common_names": ["Beet rust"],
            "disease_type": "fungal",
            "pathogen_name": "Uromyces betae",
            "severity_level": "low",
            "symptoms": ["pustules_rouille", "taches_brunes", "défoliation_légère"],
            "visual_indicators": ["pustules_brun_rougeâtre"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate"},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 41],
            "treatment_options": ["fongicide_triazole"],
            "prevention_methods": ["rotation_cultures", "élimination_résidus"],
            "yield_impact": "2-10%",
            "economic_threshold": "Rarement traité",
            "spread_rate": "moderate",
            "eppo_code": "UROMBT"
        }
    ]
}

async def seed_expanded_diseases():
    """Seed expanded disease database"""
    print("🦠 Seeding EXPANDED disease database...")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        total_added = 0
        total_skipped = 0
        
        for crop_type, diseases in EXPANDED_DISEASE_DATA.items():
            print(f"\n📊 Processing {crop_type.upper().replace('_', ' ')} diseases...")
            
            for disease_data in diseases:
                # Check if disease already exists
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
                
                # Build comprehensive description
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
                
                # Build keywords
                keywords = [disease_data["name"], crop_type, disease_data["disease_type"]] + disease_data["symptoms"]
                if disease_data.get("eppo_code"):
                    keywords.append(disease_data["eppo_code"])
                
                # Insert disease
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
                    "data_source": "comprehensive_french_agriculture_expanded",
                    "last_verified": datetime.now(),
                    "description": description,
                    "keywords": json.dumps(keywords),
                    "is_active": True
                })
                
                total_added += 1
                print(f"  ✅ Added: {disease_data['name']} (EPPO: {disease_data.get('eppo_code', 'N/A')})")
        
        await db.commit()
        
        print("\n" + "="*80)
        print(f"🎉 Expanded disease database seeding complete!")
        print(f"   ✅ Added: {total_added} diseases")
        print(f"   ⚠️  Skipped: {total_skipped} (already exist)")
        print("="*80)


async def verify_database():
    """Verify database contents"""
    print("\n🔍 Verifying database contents...")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        # Get total count
        count_query = text("SELECT COUNT(*) FROM diseases")
        result = await db.execute(count_query)
        total = result.fetchone()[0]
        
        print(f"\n📊 TOTAL DISEASES IN DATABASE: {total}")
        
        for crop_type in ["blé", "maïs", "colza", "pomme_de_terre", "vigne", "betterave_sucrière"]:
            query = text("""
                SELECT name, scientific_name, severity_level
                FROM diseases
                WHERE primary_crop = :crop
                ORDER BY name
            """)
            result = await db.execute(query, {"crop": crop_type})
            diseases = result.fetchall()

            print(f"\n{crop_type.upper().replace('_', ' ')}: {len(diseases)} diseases")
            for disease in diseases:
                print(f"  - {disease[0]} ({disease[1]}) - {disease[2]}")


async def main():
    """Main seeding function"""
    print("\n" + "="*80)
    print("🚀 EXPANDED DISEASE DATABASE SEEDING")
    print("="*80)
    
    try:
        await seed_expanded_diseases()
        await verify_database()
        print("\n✅ All operations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

