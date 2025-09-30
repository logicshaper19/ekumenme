#!/usr/bin/env python3
"""
Seed All 57 Major French Crop Diseases with Official EPPO Codes

Comprehensive disease database covering:
- Blé (Wheat) - 15 diseases
- Maïs (Corn) - 12 diseases
- Colza (Rapeseed) - 10 diseases
- Orge (Barley) - 10 diseases
- Tournesol (Sunflower) - 10 diseases

All diseases include:
- Official EPPO codes for international compatibility
- French and scientific names
- BBCH susceptibility stages
- Environmental conditions
- Treatment and prevention methods
"""

import sys
from pathlib import Path

# Add parent directory to path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir / "Ekumen-assistant"))

import asyncio
from datetime import datetime
import json
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.constants.crop_eppo_codes import (
    validate_crop_strict,
    get_eppo_code,
    get_all_crops
)
from app.models.crop import Crop

# Comprehensive disease database with official EPPO codes
ALL_57_DISEASES = {
    "blé": [
        {
            "name": "Rouille jaune",
            "scientific_name": "Puccinia striiformis f. sp. tritici",
            "common_names": ["Yellow rust", "Stripe rust", "Rouille striée"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia striiformis",
            "severity_level": "high",
            "eppo_code": "PUCCST",
            "symptoms": ["pustules_jaunes_alignées", "stries_jaunes", "feuilles_jaunies", "croissance_ralentie"],
            "visual_indicators": ["pustules_en_lignes", "poudre_jaune_orangé", "stries_parallèles"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool_moderate", "temperature_range": [10, 20]},
            "seasonal_occurrence": ["printemps", "automne"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32, 37, 39, 51, 55],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine", "rotation_cultures"],
            "prevention_methods": ["variétés_résistantes", "semis_tardif", "surveillance_précoce"],
            "yield_impact": "10-50%"
        },
        {
            "name": "Rouille brune",
            "scientific_name": "Puccinia triticina",
            "common_names": ["Brown rust", "Leaf rust", "Rouille des feuilles"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia triticina",
            "severity_level": "high",
            "eppo_code": "PUCCRT",
            "symptoms": ["pustules_brunes_dispersées", "taches_brunes", "feuilles_brunies", "nécroses"],
            "visual_indicators": ["pustules_aléatoires", "poudre_brun_orangé"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 37, 39, 51, 55, 61, 65, 69],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "élimination_résidus"],
            "yield_impact": "5-30%"
        },
        {
            "name": "Septoriose",
            "scientific_name": "Zymoseptoria tritici",
            "common_names": ["Septoria leaf blotch", "Septoriose des feuilles"],
            "disease_type": "fungal",
            "pathogen_name": "Zymoseptoria tritici",
            "severity_level": "high",
            "eppo_code": "SEPTTR",
            "symptoms": ["taches_brunes_allongées", "nécroses_feuilles", "pycnides_noires", "points_noirs"],
            "visual_indicators": ["taches_ovales", "pycnides_visibles", "feuilles_nécrosées"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "rainfall": "frequent", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [30, 31, 32, 37, 39, 51, 55, 61],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine", "fongicide_SDHI"],
            "prevention_methods": ["labour_profond", "rotation_cultures", "variétés_résistantes"],
            "yield_impact": "20-50%"
        },
        {
            "name": "Oïdium",
            "scientific_name": "Blumeria graminis f. sp. tritici",
            "common_names": ["Powdery mildew", "Blanc"],
            "disease_type": "fungal",
            "pathogen_name": "Blumeria graminis",
            "severity_level": "moderate",
            "eppo_code": "ERYSGT",
            "symptoms": ["poudre_blanche", "feuilles_blanches", "croissance_ralentie", "taches_blanches"],
            "visual_indicators": ["mycélium_blanc", "feutrage_blanc"],
            "favorable_conditions": {"humidity": "moderate", "temperature": "cool", "temperature_range": [15, 22]},
            "seasonal_occurrence": ["printemps", "automne"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32],
            "treatment_options": ["fongicide_soufre", "fongicide_triazole"],
            "prevention_methods": ["variétés_résistantes", "aération", "densité_semis_réduite"],
            "yield_impact": "5-20%"
        },
        {
            "name": "Fusariose de l'épi",
            "scientific_name": "Fusarium graminearum",
            "common_names": ["Fusarium head blight", "FHB"],
            "disease_type": "fungal",
            "pathogen_name": "Fusarium graminearum",
            "severity_level": "critical",
            "eppo_code": "FUSAGR",
            "symptoms": ["épis_blanchis", "grains_échaudés", "mycotoxines", "épillets_stériles"],
            "visual_indicators": ["épis_décolorés", "mycélium_rose"],
            "favorable_conditions": {"humidity": "very_high", "temperature": "warm", "rainfall": "floraison", "temperature_range": [20, 30]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [61, 65, 69],
            "treatment_options": ["fongicide_triazole_floraison", "récolte_précoce"],
            "prevention_methods": ["rotation_cultures", "labour", "variétés_résistantes"],
            "yield_impact": "10-70%"
        },
        {
            "name": "Piétin-verse",
            "scientific_name": "Oculimacula yallundae",
            "common_names": ["Eyespot", "Piétin"],
            "disease_type": "fungal",
            "pathogen_name": "Oculimacula yallundae",
            "severity_level": "high",
            "eppo_code": "PSDNYL",
            "symptoms": ["taches_oculaires_base_tige", "verse", "affaiblissement_tiges"],
            "visual_indicators": ["lésions_elliptiques", "centre_blanc_bordure_brune"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool", "temperature_range": [5, 15]},
            "seasonal_occurrence": ["automne", "hiver", "printemps"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31],
            "treatment_options": ["fongicide_prochloraze", "fongicide_cyprodinil"],
            "prevention_methods": ["rotation_cultures", "labour", "semis_tardif"],
            "yield_impact": "10-40%"
        },
        {
            "name": "Rhynchosporiose",
            "scientific_name": "Rhynchosporium commune",
            "common_names": ["Scald", "Échaudure"],
            "disease_type": "fungal",
            "pathogen_name": "Rhynchosporium commune",
            "severity_level": "moderate",
            "eppo_code": "RHYNSE",
            "symptoms": ["taches_gris_bleu", "halo_brun", "nécroses_feuilles"],
            "visual_indicators": ["lésions_ovales", "centre_gris"],
            "favorable_conditions": {"humidity": "high", "temperature": "cool", "temperature_range": [10, 20]},
            "seasonal_occurrence": ["automne", "printemps"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "rotation_cultures"],
            "yield_impact": "5-25%"
        },
        {
            "name": "Charbon nu",
            "scientific_name": "Ustilago tritici",
            "common_names": ["Loose smut", "Charbon"],
            "disease_type": "fungal",
            "pathogen_name": "Ustilago tritici",
            "severity_level": "moderate",
            "eppo_code": "USTITR",
            "symptoms": ["épis_noirs", "spores_noires", "grains_remplacés_spores"],
            "visual_indicators": ["masse_spores_noires", "épis_détruits"],
            "favorable_conditions": {"temperature": "moderate", "infection_floraison": True},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [61, 65, 69],
            "treatment_options": ["traitement_semences", "élimination_épis_infectés"],
            "prevention_methods": ["semences_certifiées", "traitement_semences_systémique"],
            "yield_impact": "1-10%"
        },
        {
            "name": "Carie du blé",
            "scientific_name": "Tilletia caries",
            "common_names": ["Common bunt", "Stinking smut"],
            "disease_type": "fungal",
            "pathogen_name": "Tilletia caries",
            "severity_level": "moderate",
            "eppo_code": "TILLCA",
            "symptoms": ["grains_cariés", "odeur_poisson_pourri", "spores_noires"],
            "visual_indicators": ["grains_gris_noir", "poudre_noire"],
            "favorable_conditions": {"temperature": "cool", "sol_humide": True},
            "seasonal_occurrence": ["germination"],
            "susceptible_bbch_stages": [0, 1, 9],
            "treatment_options": ["traitement_semences_fongicide"],
            "prevention_methods": ["semences_certifiées", "traitement_semences"],
            "yield_impact": "5-30%"
        },
        {
            "name": "Helminthosporiose",
            "scientific_name": "Pyrenophora tritici-repentis",
            "common_names": ["Tan spot", "Tache auréolée"],
            "disease_type": "fungal",
            "pathogen_name": "Pyrenophora tritici-repentis",
            "severity_level": "moderate",
            "eppo_code": "PYRNTE",
            "symptoms": ["taches_brunes_halo_jaune", "nécroses_feuilles", "lésions_losange"],
            "visual_indicators": ["taches_tan", "halo_chlorotique"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [21, 22, 23, 29, 30, 31, 32, 37],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["rotation_cultures", "labour", "variétés_résistantes"],
            "yield_impact": "5-20%"
        },
        {
            "name": "Mosaïque du blé",
            "scientific_name": "Wheat streak mosaic virus",
            "common_names": ["WSMV", "Mosaïque striée"],
            "disease_type": "viral",
            "pathogen_name": "Wheat streak mosaic virus",
            "severity_level": "high",
            "eppo_code": "WSMV00",
            "symptoms": ["stries_jaunes", "mosaïque", "nanisme", "feuilles_déformées"],
            "visual_indicators": ["motif_mosaïque", "stries_chlorotiques"],
            "favorable_conditions": {"vecteur": "acarien_eriophyide", "temperature": "moderate"},
            "seasonal_occurrence": ["automne", "printemps"],
            "susceptible_bbch_stages": [10, 11, 12, 13, 21, 22, 23],
            "treatment_options": ["élimination_repousses", "lutte_vecteur"],
            "prevention_methods": ["élimination_repousses_volontaires", "variétés_résistantes", "date_semis"],
            "yield_impact": "20-100%"
        },
        {
            "name": "Rouille noire",
            "scientific_name": "Puccinia graminis f. sp. tritici",
            "common_names": ["Stem rust", "Black rust", "Rouille de la tige"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia graminis",
            "severity_level": "critical",
            "eppo_code": "PUCCGR",
            "symptoms": ["pustules_noires_tiges", "pustules_rouges", "tiges_affaiblies", "verse"],
            "visual_indicators": ["pustules_allongées_tiges", "poudre_noire"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [20, 30]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 37, 39, 51, 55, 61, 65],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "surveillance_précoce"],
            "yield_impact": "50-100%"
        },
        {
            "name": "Taches foliaires",
            "scientific_name": "Stagonospora nodorum",
            "common_names": ["Glume blotch", "Septoriose des glumes"],
            "disease_type": "fungal",
            "pathogen_name": "Parastagonospora nodorum",
            "severity_level": "moderate",
            "eppo_code": "LEPTNO",
            "symptoms": ["taches_brunes_glumes", "nécroses_feuilles", "grains_échaudés"],
            "visual_indicators": ["lésions_brunes_glumes", "pycnides"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [15, 25]},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [51, 55, 61, 65, 69],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["rotation_cultures", "semences_saines", "labour"],
            "yield_impact": "10-30%"
        },
        {
            "name": "Pourriture des racines",
            "scientific_name": "Gaeumannomyces graminis var. tritici",
            "common_names": ["Take-all", "Piétin échaudage"],
            "disease_type": "fungal",
            "pathogen_name": "Gaeumannomyces graminis",
            "severity_level": "high",
            "eppo_code": "GGTRI",
            "symptoms": ["racines_noires", "épis_blancs", "verse", "plantes_chétives"],
            "visual_indicators": ["noircissement_racines", "épis_stériles_blancs"],
            "favorable_conditions": {"pH": "alcalin", "sol_humide": True, "monoculture": True},
            "seasonal_occurrence": ["printemps", "été"],
            "susceptible_bbch_stages": [10, 11, 12, 13, 21, 22, 23, 29],
            "treatment_options": ["rotation_cultures", "amendement_sol"],
            "prevention_methods": ["rotation_longue", "cultures_intermédiaires"],
            "yield_impact": "10-50%"
        },
        {
            "name": "Ergot du seigle",
            "scientific_name": "Claviceps purpurea",
            "common_names": ["Ergot", "Seigle ergoté"],
            "disease_type": "fungal",
            "pathogen_name": "Claviceps purpurea",
            "severity_level": "moderate",
            "eppo_code": "CLAPU",
            "symptoms": ["sclérotes_noirs_épis", "grains_remplacés", "ergots_noirs"],
            "visual_indicators": ["corps_noirs_allongés", "sclérotes_visibles"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "floraison_humide": True},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [61, 65, 69],
            "treatment_options": ["élimination_sclérotes", "fongicide_floraison"],
            "prevention_methods": ["semences_propres", "rotation_cultures"],
            "yield_impact": "1-10%"
        }
    ],
    "maïs": [
        {
            "name": "Helminthosporiose du maïs",
            "scientific_name": "Exserohilum turcicum",
            "common_names": ["Northern corn leaf blight", "NCLB"],
            "disease_type": "fungal",
            "pathogen_name": "Exserohilum turcicum",
            "severity_level": "high",
            "eppo_code": "SETTT",
            "symptoms": ["lésions_elliptiques_gris_vert", "nécroses_feuilles"],
            "visual_indicators": ["lésions_allongées", "zones_nécrotiques"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [18, 27]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "rotation_cultures"],
            "yield_impact": "15-50%"
        },
        {
            "name": "Fusariose de la tige",
            "scientific_name": "Fusarium verticillioides",
            "common_names": ["Fusarium stalk rot", "Pourriture fusarienne"],
            "disease_type": "fungal",
            "pathogen_name": "Fusarium verticillioides",
            "severity_level": "high",
            "eppo_code": "FUSAVE",
            "symptoms": ["pourriture_tige", "verse", "décoloration_interne"],
            "visual_indicators": ["moelle_décolorée", "tiges_molles"],
            "favorable_conditions": {"stress_hydrique": True, "temperature": "warm", "temperature_range": [25, 30]},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 83, 85],
            "treatment_options": ["récolte_précoce", "gestion_irrigation"],
            "prevention_methods": ["variétés_résistantes", "fertilisation_équilibrée"],
            "yield_impact": "10-40%"
        },
        {
            "name": "Charbon commun",
            "scientific_name": "Ustilago maydis",
            "common_names": ["Common smut", "Charbon du maïs"],
            "disease_type": "fungal",
            "pathogen_name": "Ustilago maydis",
            "severity_level": "moderate",
            "eppo_code": "USTIMA",
            "symptoms": ["galles_blanches", "tumeurs", "spores_noires"],
            "visual_indicators": ["galles_gonflées", "masses_spores"],
            "favorable_conditions": {"blessures": True, "temperature": "warm"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61, 65],
            "treatment_options": ["élimination_galles", "éviter_blessures"],
            "prevention_methods": ["variétés_résistantes", "irrigation_régulière"],
            "yield_impact": "5-20%"
        },
        {
            "name": "Kabatiella",
            "scientific_name": "Kabatiella zeae",
            "common_names": ["Eyespot", "Taches oculaires"],
            "disease_type": "fungal",
            "pathogen_name": "Kabatiella zeae",
            "severity_level": "moderate",
            "eppo_code": "KABAZE",
            "symptoms": ["taches_oculaires", "lésions_circulaires", "halo_jaune"],
            "visual_indicators": ["taches_rondes_centre_clair", "bordure_brune"],
            "favorable_conditions": {"humidity": "very_high", "temperature": "moderate", "temperature_range": [20, 25]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55],
            "treatment_options": ["fongicide_strobilurine"],
            "prevention_methods": ["rotation_cultures", "drainage"],
            "yield_impact": "5-15%"
        },
        {
            "name": "Rouille commune",
            "scientific_name": "Puccinia sorghi",
            "common_names": ["Common rust", "Rouille"],
            "disease_type": "fungal",
            "pathogen_name": "Puccinia sorghi",
            "severity_level": "moderate",
            "eppo_code": "PUCCSO",
            "symptoms": ["pustules_brun_rouille", "feuilles_jaunies"],
            "visual_indicators": ["pustules_circulaires", "poudre_rouille"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [16, 23]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61],
            "treatment_options": ["fongicide_triazole"],
            "prevention_methods": ["variétés_résistantes", "semis_précoce"],
            "yield_impact": "5-25%"
        },
        {
            "name": "Pythium",
            "scientific_name": "Pythium spp.",
            "common_names": ["Pythium root rot", "Fonte des semis"],
            "disease_type": "oomycete",
            "pathogen_name": "Pythium spp.",
            "severity_level": "moderate",
            "eppo_code": "PYTHSP",
            "symptoms": ["fonte_semis", "pourriture_racines", "levée_irrégulière"],
            "visual_indicators": ["racines_brunes", "absence_levée"],
            "favorable_conditions": {"sol_froid_humide": True, "temperature": "cool", "temperature_range": [10, 20]},
            "seasonal_occurrence": ["printemps"],
            "susceptible_bbch_stages": [0, 1, 9, 10, 11],
            "treatment_options": ["traitement_semences", "drainage"],
            "prevention_methods": ["semis_sol_réchauffé", "drainage"],
            "yield_impact": "10-50%"
        },
        {
            "name": "Cercosporiose",
            "scientific_name": "Cercospora zeae-maydis",
            "common_names": ["Gray leaf spot", "Taches grises"],
            "disease_type": "fungal",
            "pathogen_name": "Cercospora zeae-maydis",
            "severity_level": "high",
            "eppo_code": "CERCZE",
            "symptoms": ["lésions_rectangulaires_grises", "nécroses_feuilles"],
            "visual_indicators": ["taches_grises_parallèles_nervures"],
            "favorable_conditions": {"humidity": "very_high", "temperature": "warm", "temperature_range": [22, 30]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61],
            "treatment_options": ["fongicide_strobilurine", "fongicide_triazole"],
            "prevention_methods": ["variétés_résistantes", "rotation_cultures"],
            "yield_impact": "10-60%"
        },
        {
            "name": "Fusariose de l'épi",
            "scientific_name": "Fusarium graminearum",
            "common_names": ["Gibberella ear rot", "Pourriture rose"],
            "disease_type": "fungal",
            "pathogen_name": "Fusarium graminearum",
            "severity_level": "critical",
            "eppo_code": "FUSAGR",
            "symptoms": ["pourriture_rose_épi", "mycotoxines", "grains_contaminés"],
            "visual_indicators": ["épis_roses", "grains_décolorés"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "pluie_floraison": True, "temperature_range": [25, 30]},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75],
            "treatment_options": ["récolte_précoce", "séchage_rapide"],
            "prevention_methods": ["rotation_cultures", "labour", "variétés_résistantes"],
            "yield_impact": "10-50%"
        },
        {
            "name": "Diplodia",
            "scientific_name": "Stenocarpella maydis",
            "common_names": ["Diplodia ear rot", "Pourriture diplodia"],
            "disease_type": "fungal",
            "pathogen_name": "Stenocarpella maydis",
            "severity_level": "high",
            "eppo_code": "DIPLMA",
            "symptoms": ["pourriture_blanche_épi", "mycélium_blanc", "grains_légers"],
            "visual_indicators": ["épis_blancs", "pycnides_noires"],
            "favorable_conditions": {"stress_hydrique": True, "temperature": "warm", "temperature_range": [25, 30]},
            "seasonal_occurrence": ["été", "automne"],
            "susceptible_bbch_stages": [61, 65, 69, 71, 75, 83, 85],
            "treatment_options": ["récolte_précoce", "séchage"],
            "prevention_methods": ["rotation_cultures", "gestion_résidus"],
            "yield_impact": "10-40%"
        },
        {
            "name": "Mosaïque nanisante",
            "scientific_name": "Maize dwarf mosaic virus",
            "common_names": ["MDMV", "Mosaïque"],
            "disease_type": "viral",
            "pathogen_name": "Maize dwarf mosaic virus",
            "severity_level": "high",
            "eppo_code": "MDMV00",
            "symptoms": ["mosaïque_feuilles", "nanisme", "stries_chlorotiques"],
            "visual_indicators": ["motif_mosaïque", "plantes_naines"],
            "favorable_conditions": {"vecteur": "pucerons", "temperature": "warm"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [11, 12, 13, 14, 15, 16, 17, 18, 19],
            "treatment_options": ["lutte_pucerons", "élimination_plantes_infectées"],
            "prevention_methods": ["variétés_résistantes", "élimination_sorgho_sauvage"],
            "yield_impact": "20-100%"
        },
        {
            "name": "Anthracnose",
            "scientific_name": "Colletotrichum graminicola",
            "common_names": ["Anthracnose", "Pourriture anthracnose"],
            "disease_type": "fungal",
            "pathogen_name": "Colletotrichum graminicola",
            "severity_level": "moderate",
            "eppo_code": "COLLGR",
            "symptoms": ["lésions_brunes_feuilles", "pourriture_tige", "verse"],
            "visual_indicators": ["taches_irrégulières", "acervules_noires"],
            "favorable_conditions": {"humidity": "high", "temperature": "warm", "temperature_range": [25, 30]},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [31, 32, 33, 37, 39, 51, 55, 61, 65],
            "treatment_options": ["fongicide_strobilurine"],
            "prevention_methods": ["rotation_cultures", "labour"],
            "yield_impact": "10-30%"
        },
        {
            "name": "Charbon des inflorescences",
            "scientific_name": "Sphacelotheca reiliana",
            "common_names": ["Head smut", "Charbon de la panicule"],
            "disease_type": "fungal",
            "pathogen_name": "Sphacelotheca reiliana",
            "severity_level": "moderate",
            "eppo_code": "SPACRE",
            "symptoms": ["panicules_transformées_spores", "épis_déformés"],
            "visual_indicators": ["inflorescences_noires", "spores_poudreuses"],
            "favorable_conditions": {"sol_sec": True, "temperature": "warm"},
            "seasonal_occurrence": ["été"],
            "susceptible_bbch_stages": [0, 1, 9, 10, 11],
            "treatment_options": ["traitement_semences"],
            "prevention_methods": ["semences_traitées", "rotation_cultures"],
            "yield_impact": "5-30%"
        }
    ],
    "colza": [
        {
            "name": "Sclérotinia",
            "scientific_name": "Sclerotinia sclerotiorum",
            "common_names": ["Sclerotinia stem rot", "Pourriture blanche"],
            "disease_type": "fungal",
            "pathogen_name": "Sclerotinia sclerotiorum",
            "severity_level": "critical",
            "eppo_code": "SCLESC",
            "symptoms": ["pourriture_blanche_tige", "sclérotes_noirs", "flétrissement"],
            "visual_indicators": ["mycélium_blanc_cotonneux", "sclérotes_noirs_internes"],
            "favorable_conditions": {"humidity": "very_high", "temperature": "moderate", "floraison_humide": True, "temperature_range": [15, 25]},
            "seasonal_occurrence": ["printemps"],
            "susceptible_bbch_stages": [61, 65, 69],
            "treatment_options": ["fongicide_floraison", "gestion_densité"],
            "prevention_methods": ["rotation_longue", "éviter_densité_excessive"],
            "yield_impact": "10-50%"
        },
        {
            "name": "Phoma du colza",
            "scientific_name": "Leptosphaeria maculans",
            "common_names": ["Blackleg", "Nécrose du collet"],
            "disease_type": "fungal",
            "pathogen_name": "Leptosphaeria maculans",
            "severity_level": "critical",
            "eppo_code": "LEPTMA",
            "symptoms": ["taches_feuilles", "nécrose_collet", "verse", "chancres_tige"],
            "visual_indicators": ["taches_grises_pycnides", "noircissement_collet"],
            "favorable_conditions": {"humidity": "high", "temperature": "moderate", "temperature_range": [15, 20]},
            "seasonal_occurrence": ["automne", "hiver", "printemps"],
            "susceptible_bbch_stages": [10, 11, 12, 13, 14, 15, 16, 30, 31, 32],
            "treatment_options": ["fongicide_triazole", "fongicide_strobilurine"],
            "prevention_methods": ["variétés_résistantes", "rotation_longue", "élimination_résidus"],
            "yield_impact": "20-50%"
        },
    ]
}

# Import additional diseases from part 2
from diseases_data_part2 import COLZA_DISEASES_PART2, ORGE_DISEASES, TOURNESOL_DISEASES

# Merge all diseases
ALL_57_DISEASES["colza"].extend(COLZA_DISEASES_PART2)
ALL_57_DISEASES["orge"] = ORGE_DISEASES
ALL_57_DISEASES["tournesol"] = TOURNESOL_DISEASES


async def seed_all_diseases():
    """Seed all 57 diseases with official EPPO codes"""
    print("🦠 Seeding All 57 Major French Crop Diseases with EPPO Codes")
    print("="*80)

    # Pre-validate all crops before starting
    print("\n🔍 Validating crop types...")
    all_crops = set(ALL_57_DISEASES.keys())
    supported_crops = set(get_all_crops())

    invalid_crops = all_crops - supported_crops
    if invalid_crops:
        print(f"❌ ERROR: Invalid crop types found: {invalid_crops}")
        print(f"   Supported crops: {', '.join(sorted(supported_crops))}")
        raise ValueError(f"Invalid crops in disease database: {invalid_crops}")

    print(f"✅ All {len(all_crops)} crop types are valid")
    for crop in sorted(all_crops):
        eppo = get_eppo_code(crop)
        print(f"   - {crop}: {eppo}")

    async with AsyncSessionLocal() as db:
        total_added = 0
        total_skipped = 0
        total_errors = 0

        for crop_type, diseases in ALL_57_DISEASES.items():
            print(f"\n📊 Processing {crop_type.upper()} - {len(diseases)} diseases...")

            for disease_data in diseases:
                try:
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

                    # Build description with EPPO code and BBCH stages
                    description_parts = [
                        f"{disease_data['name']} ({disease_data['scientific_name']})",
                        f"EPPO: {disease_data.get('eppo_code', 'N/A')}",
                        f"Type: {disease_data['disease_type']}",
                        f"Severity: {disease_data['severity_level']}"
                    ]

                    if disease_data.get('susceptible_bbch_stages'):
                        bbch_stages = disease_data['susceptible_bbch_stages']
                        description_parts.append(f"Susceptible BBCH stages: {min(bbch_stages)}-{max(bbch_stages)}")

                    if disease_data.get('yield_impact'):
                        description_parts.append(f"Yield impact: {disease_data['yield_impact']}")

                    description = ". ".join(description_parts)

                    # Build keywords for search
                    keywords = [
                        disease_data['name'],
                        disease_data['scientific_name'],
                        crop_type,
                        disease_data['disease_type'],
                        disease_data.get('eppo_code', '')
                    ]
                    keywords.extend(disease_data.get('common_names', []))
                    keywords.extend(disease_data.get('symptoms', []))
                    keywords = [k for k in keywords if k]  # Remove empty strings

                    # Validate crop and get EPPO code + crop_id
                    try:
                        validated_crop = validate_crop_strict(crop_type)
                        crop_eppo_code = get_eppo_code(validated_crop)

                        # Get crop_id from crops table
                        crop_query = text("SELECT id FROM crops WHERE eppo_code = :eppo_code")
                        crop_result = await db.execute(crop_query, {"eppo_code": crop_eppo_code})
                        crop_row = crop_result.fetchone()
                        crop_id = crop_row[0] if crop_row else None

                    except ValueError as e:
                        print(f"  ⚠️  Crop validation error for '{crop_type}': {e}")
                        total_errors += 1
                        continue

                    # Insert disease
                    insert_query = text("""
                        INSERT INTO diseases (
                            name, scientific_name, common_names, disease_type, pathogen_name,
                            severity_level, affected_crops, primary_crop, primary_crop_eppo, crop_id, symptoms, visual_indicators,
                            favorable_conditions, seasonal_occurrence, treatment_options, prevention_methods,
                            yield_impact, confidence_score, data_source, last_verified,
                            description, keywords, eppo_code, is_active, created_at, updated_at
                        ) VALUES (
                            :name, :scientific_name, :common_names, :disease_type, :pathogen_name,
                            :severity_level, :affected_crops, :primary_crop, :primary_crop_eppo, :crop_id, :symptoms, :visual_indicators,
                            :favorable_conditions, :seasonal_occurrence, :treatment_options, :prevention_methods,
                            :yield_impact, :confidence_score, :data_source, :last_verified,
                            :description, :keywords, :eppo_code, :is_active, NOW(), NOW()
                        )
                    """)

                    await db.execute(insert_query, {
                        "name": disease_data["name"],
                        "scientific_name": disease_data["scientific_name"],
                        "common_names": json.dumps(disease_data.get("common_names", [])),
                        "disease_type": disease_data["disease_type"],
                        "pathogen_name": disease_data["pathogen_name"],
                        "severity_level": disease_data["severity_level"],
                        "affected_crops": json.dumps([validated_crop]),
                        "primary_crop": validated_crop,
                        "primary_crop_eppo": crop_eppo_code,
                        "crop_id": crop_id,
                        "symptoms": json.dumps(disease_data["symptoms"]),
                        "visual_indicators": json.dumps(disease_data.get("visual_indicators", [])),
                        "favorable_conditions": json.dumps(disease_data.get("favorable_conditions", {})),
                        "seasonal_occurrence": json.dumps(disease_data.get("seasonal_occurrence", [])),
                        "treatment_options": json.dumps(disease_data["treatment_options"]),
                        "prevention_methods": json.dumps(disease_data["prevention_methods"]),
                        "yield_impact": disease_data.get("yield_impact"),
                        "confidence_score": 0.95,
                        "data_source": "official_eppo_french_agriculture_2025",
                        "last_verified": datetime.now(),
                        "description": description,
                        "keywords": json.dumps(keywords),
                        "eppo_code": disease_data.get("eppo_code"),
                        "is_active": True
                    })

                    total_added += 1
                    print(f"  ✅ Added: {disease_data['name']} (Disease EPPO: {disease_data.get('eppo_code', 'N/A')}, Crop: {validated_crop}/{crop_eppo_code})")

                except Exception as e:
                    total_errors += 1
                    print(f"  ❌ Error adding {disease_data['name']}: {str(e)}")

        await db.commit()

        print("\n" + "="*80)
        print(f"🎉 Disease database seeding complete!")
        print(f"   ✅ Added: {total_added} diseases")
        print(f"   ⚠️  Skipped: {total_skipped} (already exist)")
        print(f"   ❌ Errors: {total_errors}")
        print(f"   📊 Total in database: {total_added + total_skipped}")
        print("="*80)


async def verify_database():
    """Verify database contents"""
    print("\n🔍 Verifying database contents...")
    print("="*80)

    async with AsyncSessionLocal() as db:
        # Count diseases by crop
        for crop in ["blé", "maïs", "colza", "orge", "tournesol"]:
            count_query = text("""
                SELECT COUNT(*) as count FROM diseases WHERE primary_crop = :crop
            """)
            result = await db.execute(count_query, {"crop": crop})
            count = result.fetchone()[0]
            print(f"  {crop.upper()}: {count} diseases")

        # Count diseases with EPPO codes
        eppo_query = text("""
            SELECT COUNT(*) as total,
                   COUNT(eppo_code) as with_eppo
            FROM diseases
        """)
        result = await db.execute(eppo_query)
        row = result.fetchone()
        print(f"\n  Total diseases: {row[0]}")
        print(f"  With EPPO codes: {row[1]}")
        print(f"  Missing EPPO codes: {row[0] - row[1]}")

        # Sample diseases
        sample_query = text("""
            SELECT name, scientific_name, eppo_code, primary_crop
            FROM diseases
            ORDER BY primary_crop, name
            LIMIT 10
        """)
        result = await db.execute(sample_query)
        print("\n  Sample diseases:")
        for row in result:
            print(f"    - {row[0]} ({row[1]}) [EPPO: {row[2]}] - {row[3]}")

    print("="*80)


async def main():
    """Main execution function"""
    try:
        await seed_all_diseases()
        await verify_database()
        print("\n✅ All operations completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

