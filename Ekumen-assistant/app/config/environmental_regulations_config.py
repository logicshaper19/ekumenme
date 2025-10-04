"""
Environmental Regulations Configuration
Extracted from check_environmental_regulations_tool.py for better maintainability
"""

from app.tools.schemas.environmental_schemas import EnvironmentalImpactLevel

# Environmental regulations database
ENVIRONMENTAL_DATABASE = {
    "spraying": {
        "water_protection": {
            "regulation_name": "Protection des eaux",
            "environmental_impact": EnvironmentalImpactLevel.HIGH,
            "required_measures": [
                "Respecter les ZNT (zones non traitées)",
                "Éviter le ruissellement vers les cours d'eau",
                "Respecter les doses homologuées",
                "Utiliser des buses anti-dérive"
            ],
            "restrictions": [
                "Interdiction de traiter à proximité immédiate des cours d'eau",
                "Interdiction de traiter en cas de pluie imminente",
                "Interdiction de rincer le matériel près des points d'eau"
            ],
            "penalties": [
                "Amende: 3000€ à 30000€",
                "Suspension de l'autorisation de traitement",
                "Responsabilité civile en cas de pollution"
            ],
            "legal_references": [
                "Code de l'environnement - Article L216-6",
                "Arrêté du 4 mai 2017 relatif aux ZNT",
                "Directive cadre sur l'eau 2000/60/CE"
            ]
        },
        "biodiversity_protection": {
            "regulation_name": "Protection de la biodiversité",
            "environmental_impact": EnvironmentalImpactLevel.MODERATE,
            "required_measures": [
                "Éviter les périodes de floraison pour protéger les abeilles",
                "Respecter les cycles de reproduction de la faune",
                "Privilégier les alternatives biologiques",
                "Maintenir des zones de biodiversité (haies, bandes enherbées)"
            ],
            "restrictions": [
                "Interdiction de traiter pendant la floraison (abeilles)",
                "Interdiction de traiter pendant la nidification (oiseaux)",
                "Restrictions en zones Natura 2000"
            ],
            "penalties": [
                "Amende: 2000€ à 15000€",
                "Compensation écologique obligatoire",
                "Suspension des aides environnementales"
            ],
            "legal_references": [
                "Code de l'environnement - Article L411-1",
                "Directive Habitats 92/43/CEE",
                "Arrêté du 28 novembre 2003 (protection des abeilles)"
            ]
        },
        "air_quality": {
            "regulation_name": "Qualité de l'air",
            "environmental_impact": EnvironmentalImpactLevel.MODERATE,
            "required_measures": [
                "Éviter la dérive de pulvérisation",
                "Traiter par vent favorable (< 19 km/h)",
                "Utiliser du matériel contrôlé et homologué",
                "Respecter les distances par rapport aux habitations"
            ],
            "restrictions": [
                "Interdiction de traiter par vent fort (> 19 km/h)",
                "Interdiction de traiter à proximité des habitations (50m minimum)",
                "Interdiction de traiter en période de forte chaleur"
            ],
            "penalties": [
                "Amende: 1500€ à 10000€",
                "Suspension de l'activité de traitement",
                "Responsabilité civile en cas de dommages"
            ],
            "legal_references": [
                "Code de l'environnement - Article L220-1",
                "Arrêté du 27 juin 2016 (distances habitations)",
                "Directive 2008/50/CE (qualité de l'air)"
            ]
        }
    },
    "fertilization": {
        "nitrate_directive": {
            "regulation_name": "Directive Nitrates",
            "environmental_impact": EnvironmentalImpactLevel.HIGH,
            "required_measures": [
                "Respecter le plafond d'azote (170 kg N/ha/an)",
                "Établir un plan d'épandage",
                "Tenir un cahier d'enregistrement",
                "Respecter les périodes d'interdiction d'épandage"
            ],
            "restrictions": [
                "Interdiction d'épandage en hiver (15 nov - 15 janv)",
                "Interdiction d'épandage à proximité des cours d'eau",
                "Interdiction d'épandage sur sol gelé ou enneigé"
            ],
            "penalties": [
                "Amende: 5000€ à 30000€",
                "Suspension des aides PAC",
                "Mise en demeure de régularisation"
            ],
            "legal_references": [
                "Directive 91/676/CEE (Directive Nitrates)",
                "Code de l'environnement - Article R211-80",
                "Arrêté du 19 décembre 2011 (programme d'actions)"
            ]
        },
        "phosphorus_management": {
            "regulation_name": "Gestion du phosphore",
            "environmental_impact": EnvironmentalImpactLevel.MODERATE,
            "required_measures": [
                "Respecter le plafond de phosphore",
                "Réaliser des analyses de sol régulières",
                "Pratiquer la rotation des cultures",
                "Éviter les apports excessifs"
            ],
            "restrictions": [
                "Interdiction d'apport en cas de surplus avéré",
                "Interdiction d'épandage à proximité des cours d'eau",
                "Restrictions en zones sensibles"
            ],
            "penalties": [
                "Amende: 3000€ à 15000€",
                "Suspension des aides environnementales",
                "Obligation de remédiation"
            ],
            "legal_references": [
                "Code de l'environnement - Article L216-6",
                "Directive cadre sur l'eau 2000/60/CE"
            ]
        }
    },
    "irrigation": {
        "water_usage": {
            "regulation_name": "Usage de l'eau",
            "environmental_impact": EnvironmentalImpactLevel.HIGH,
            "required_measures": [
                "Installer un compteur d'eau",
                "Respecter le plafond d'usage autorisé",
                "Optimiser l'efficacité de l'irrigation",
                "Déclarer les prélèvements"
            ],
            "restrictions": [
                "Interdiction d'irrigation en période de sécheresse",
                "Restrictions horaires en été (irrigation nocturne)",
                "Interdiction de prélèvement en période d'étiage"
            ],
            "penalties": [
                "Amende: 2000€ à 15000€",
                "Suspension de l'autorisation de prélèvement",
                "Réduction des quotas d'eau"
            ],
            "legal_references": [
                "Code de l'environnement - Article L211-3",
                "Arrêté préfectoral d'autorisation de prélèvement",
                "Directive cadre sur l'eau 2000/60/CE"
            ]
        },
        "groundwater_protection": {
            "regulation_name": "Protection des eaux souterraines",
            "environmental_impact": EnvironmentalImpactLevel.CRITICAL,
            "required_measures": [
                "Éviter la contamination des nappes phréatiques",
                "Respecter les zones de protection des captages",
                "Utiliser des techniques d'irrigation économes",
                "Surveiller la qualité des eaux souterraines"
            ],
            "restrictions": [
                "Interdiction d'irrigation à proximité des captages d'eau potable",
                "Interdiction d'utilisation d'eaux usées non traitées",
                "Restrictions en zones de protection des captages"
            ],
            "penalties": [
                "Amende: 10000€ à 50000€",
                "Suspension définitive de l'autorisation",
                "Responsabilité civile et pénale en cas de pollution"
            ],
            "legal_references": [
                "Code de la santé publique - Article L1321-2",
                "Code de l'environnement - Article L211-3",
                "Directive 2006/118/CE (eaux souterraines)"
            ]
        }
    }
}

# ZNT reduction rates by equipment class
ZNT_REDUCTION_RATES = {
    "NO_EQUIPMENT": 0.0,
    "ONE_STAR": 0.25,
    "THREE_STAR": 0.33,
    "FIVE_STAR": 0.50
}

# Minimum ZNT by water body type
MIN_ZNT_BY_WATER_BODY_TYPE = {
    "PERMANENT_STREAM": 5.0,
    "INTERMITTENT_STREAM": 5.0,
    "LAKE_POND": 5.0,
    "WETLAND": 5.0,
    "DRAINAGE_DITCH": 1.0,
    "UNKNOWN": 5.0
}

# Water body classification rules
WATER_BODY_RULES = {
    "DRINKING_WATER_SOURCE": {
        "base_znt_m": 200.0,
        "reduction_allowed": False,
        "special_protections": [
            "Périmètre de protection rapprochée (PPR)",
            "Interdiction totale de produits phytosanitaires",
            "Autorisation préfectorale requise pour toute intervention",
            "Sanctions pénales en cas de pollution"
        ],
        "is_drinking_water_source": True,
        "is_fish_bearing": True
    },
    "PERMANENT_STREAM": {
        "base_znt_m": 5.0,
        "reduction_allowed": True,
        "special_protections": [
            "Respecter les ZNT obligatoires",
            "Éviter le ruissellement direct"
        ],
        "is_drinking_water_source": False,
        "is_fish_bearing": True
    },
    "INTERMITTENT_STREAM": {
        "base_znt_m": 5.0,
        "reduction_allowed": True,
        "special_protections": [
            "Respecter les ZNT obligatoires",
            "Éviter le ruissellement direct"
        ],
        "is_drinking_water_source": False,
        "is_fish_bearing": False
    },
    "LAKE_POND": {
        "base_znt_m": 5.0,
        "reduction_allowed": True,
        "special_protections": [
            "Respecter les ZNT obligatoires",
            "Éviter le ruissellement direct"
        ],
        "is_drinking_water_source": False,
        "is_fish_bearing": True
    },
    "WETLAND": {
        "base_znt_m": 5.0,
        "reduction_allowed": True,
        "special_protections": [
            "Respecter les ZNT obligatoires",
            "Protection de la biodiversité"
        ],
        "is_drinking_water_source": False,
        "is_fish_bearing": False
    },
    "DRAINAGE_DITCH": {
        "base_znt_m": 1.0,
        "reduction_allowed": True,
        "special_protections": [
            "Respecter les ZNT obligatoires"
        ],
        "is_drinking_water_source": False,
        "is_fish_bearing": False
    },
    "UNKNOWN": {
        "base_znt_m": 5.0,
        "reduction_allowed": True,
        "special_protections": [
            "Respecter les ZNT obligatoires"
        ],
        "is_drinking_water_source": False,
        "is_fish_bearing": False
    }
}

# Risk assessment weights
RISK_WEIGHTS = {
    "impact_weight": {
        "LOW": 0.1,
        "MODERATE": 0.3,
        "HIGH": 0.6,
        "CRITICAL": 1.0
    },
    "compliance_weight": {
        "COMPLIANT": 0.1,
        "PARTIALLY_COMPLIANT": 0.5,
        "NON_COMPLIANT": 1.0,
        "UNKNOWN": 0.3
    }
}
