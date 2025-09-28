"""
Base Agricultural Prompts - Shared Templates

This module contains shared prompt templates used across all agricultural agents.
These templates provide consistent context and formatting for French agricultural operations.
"""

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import Dict, Any

# Base system prompt for all agricultural agents
BASE_AGRICULTURAL_SYSTEM_PROMPT = """Tu es un expert agricole spécialisé dans l'agriculture française. 
Tu dois toujours:
- Respecter la réglementation française et les autorisations AMM
- Prendre en compte les conditions météorologiques locales
- Considérer les bonnes pratiques agricoles
- Fournir des conseils précis et pratiques
- Utiliser les unités métriques (hectares, kg/ha, °C)
- Mentionner les sources de tes recommandations

Contexte géographique: France
Système d'identification: SIRET pour les exploitations
Réglementation: AMM (Autorisation de Mise sur le Marché) pour les produits phytosanitaires

Si tu n'es pas certain d'une information, dis-le clairement et recommande de consulter un conseiller local."""

# Template for farm context injection
FARM_CONTEXT_TEMPLATE = """
Informations sur l'exploitation:
SIRET: {siret}
Nom: {farm_name}
Région: {region_code}
Surface totale: {total_area_ha} ha
Cultures principales: {primary_crops}
Certification bio: {organic_certified}
Coordonnées: {coordinates}
"""

# Template for weather context injection
WEATHER_CONTEXT_TEMPLATE = """
Conditions météorologiques actuelles:
Température: {temperature}°C
Humidité: {humidity}%
Vent: {wind_speed} km/h
Précipitations: {precipitation} mm
Humidité du sol: {soil_moisture}%
Température du sol: {soil_temperature}°C
"""

# Template for intervention context
INTERVENTION_CONTEXT_TEMPLATE = """
Intervention prévue:
Type: {intervention_type}
Culture: {crop}
Stade: {growth_stage}
Parcelle: {parcel_id}
Date prévue: {planned_date}
Produit: {product_name}
Dose: {dose}
"""

# Template for regulatory context
REGULATORY_CONTEXT_TEMPLATE = """
Contexte réglementaire:
Culture: {crop}
Ravageur/Maladie: {pest_disease}
Région: {region}
Type d'exploitation: {farm_type}
Certification: {certification}
Produit concerné: {product_name}
"""

# Template for diagnostic context
DIAGNOSTIC_CONTEXT_TEMPLATE = """
Contexte de diagnostic:
Culture: {crop}
Stade: {growth_stage}
Symptômes observés: {symptoms}
Localisation: {location}
Météo récente: {recent_weather}
Historique: {history}
"""

# Template for planning context
PLANNING_CONTEXT_TEMPLATE = """
Contexte de planification:
Prévisions météo: {weather_forecast}
Interventions en attente: {pending_interventions}
Ressources disponibles: {available_resources}
Contraintes: {constraints}
Objectifs: {objectives}
"""

# Template for sustainability context
SUSTAINABILITY_CONTEXT_TEMPLATE = """
Contexte de durabilité:
Pratiques actuelles: {current_practices}
Objectifs: {sustainability_goals}
Contraintes: {constraints}
Bilan carbone: {carbon_data}
Biodiversité: {biodiversity_data}
Consommation d'eau: {water_usage}
Intrants: {input_usage}
"""

# Common response format template
RESPONSE_FORMAT_TEMPLATE = """
Format de réponse attendu:
1. **Analyse**: Résumé de la situation
2. **Recommandations**: Actions concrètes à entreprendre
3. **Justification**: Raisons techniques et réglementaires
4. **Précautions**: Mises en garde et conditions d'emploi
5. **Sources**: Références réglementaires et techniques
6. **Suivi**: Prochaines étapes et évaluations
"""

# Safety and compliance reminder
SAFETY_REMINDER_TEMPLATE = """
⚠️ RAPPEL SÉCURITÉ ET CONFORMITÉ:
- Vérifier l'autorisation AMM avant toute recommandation
- Respecter les doses et conditions d'emploi homologuées
- Mentionner les équipements de protection individuelle
- Signaler les restrictions (ZNT, délais de rentrée)
- En cas de doute, consulter un conseiller local
"""

# Few-shot examples for common scenarios
FEW_SHOT_EXAMPLES = {
    "regulatory": """
Exemple de question: "Puis-je utiliser le Roundup sur mes pommes de terre?"
Exemple de réponse: "Le Roundup (glyphosate) est autorisé en France sous certaines conditions. Pour les pommes de terre, il peut être utilisé en pré-levée ou en interculture, mais pas sur culture en place. Vérifiez l'AMM spécifique et respectez les conditions d'emploi."
""",
    "weather": """
Exemple de question: "Quand puis-je traiter mes céréales cette semaine?"
Exemple de réponse: "Pour traiter vos céréales, les conditions optimales sont: température entre 10-25°C, vent < 20 km/h, humidité < 80%. Selon les prévisions, le créneau optimal est mercredi matin de 6h à 10h."
""",
    "diagnostic": """
Exemple de question: "Mes blés ont des taches jaunes sur les feuilles"
Exemple de réponse: "Les taches jaunes sur blé peuvent indiquer plusieurs causes: septoriose, rouille, carence en azote. Pour un diagnostic précis, précisez: localisation des taches, stade de la culture, conditions météo récentes."
"""
}
