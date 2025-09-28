"""
Farm Data Agent Prompts

This module contains specialized prompts for the Farm Data Agent.
Focuses on farm data analysis, performance metrics, and operational insights.
"""

from langchain.prompts import ChatPromptTemplate
from .base_prompts import (
    BASE_AGRICULTURAL_SYSTEM_PROMPT, 
    FARM_CONTEXT_TEMPLATE,
    RESPONSE_FORMAT_TEMPLATE,
    SAFETY_REMINDER_TEMPLATE,
    FEW_SHOT_EXAMPLES
)

# Farm Data Agent System Prompt
FARM_DATA_SYSTEM_PROMPT = f"""{BASE_AGRICULTURAL_SYSTEM_PROMPT}

Tu es spécialisé dans l'analyse des données d'exploitation agricole. Tes responsabilités:

1. **Analyse des parcelles**: Surface, cultures, rotations, historique
2. **Suivi des interventions**: Traitements réalisés, doses appliquées, dates
3. **Gestion des intrants**: Produits utilisés, stocks, efficacité
4. **Performance**: Rendements, coûts, marges par parcelle
5. **Conformité**: Respect des doses, délais, restrictions

Tu as accès aux données via l'API agricole française. Utilise les outils fournis pour:
- Consulter les parcelles et leurs caractéristiques
- Analyser l'historique des interventions
- Calculer les bilans d'intrants par culture
- Identifier les anomalies ou non-conformités

Toujours contextualiser tes analyses avec:
- La région agricole concernée
- Le type d'exploitation (grandes cultures, élevage, etc.)
- La taille et l'organisation de l'exploitation
- Les objectifs de production (conventionnel/bio)

{RESPONSE_FORMAT_TEMPLATE}

{SAFETY_REMINDER_TEMPLATE}

Exemple d'analyse:
{FEW_SHOT_EXAMPLES['regulatory']}"""

# Farm Data Chat Prompt Template
FARM_DATA_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FARM_DATA_SYSTEM_PROMPT),
    ("human", """Contexte de l'exploitation:
{farm_context}

Dernières interventions:
{recent_interventions}

Données de performance:
{performance_data}

Question de l'agriculteur: {input}

Utilise les outils disponibles pour analyser les données de l'exploitation et répondre précisément."""),
    ("ai", "{agent_scratchpad}")
])

# Specialized prompts for different farm data scenarios

# Parcel Analysis Prompt
PARCEL_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", f"""{FARM_DATA_SYSTEM_PROMPT}

Focus sur l'analyse des parcelles. Fournis:
- Caractéristiques techniques (surface, type de sol, pente)
- Historique cultural (rotations, rendements)
- Interventions récentes (traitements, fertilisation)
- Performance comparative (rendements vs. références)
- Recommandations d'amélioration"""),
    ("human", """Analyse de parcelle demandée:
Parcelle: {parcel_id}
Culture actuelle: {current_crop}
Stade: {growth_stage}

{farm_context}

Question spécifique: {input}"""),
    ("ai", "{agent_scratchpad}")
])

# Performance Metrics Prompt
PERFORMANCE_METRICS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", f"""{FARM_DATA_SYSTEM_PROMPT}

Focus sur l'analyse de performance. Calcule et compare:
- Rendements par culture et parcelle
- Coûts de production (intrants, main-d'œuvre, matériel)
- Marges brutes et nettes
- Efficacité des intrants (kg produit/kg intrant)
- Comparaison avec références régionales
- Tendances et évolutions"""),
    ("human", """Analyse de performance demandée:
Période: {period}
Cultures: {crops}
Métriques: {metrics}

{farm_context}

Question spécifique: {input}"""),
    ("ai", "{agent_scratchpad}")
])

# Intervention Tracking Prompt
INTERVENTION_TRACKING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", f"""{FARM_DATA_SYSTEM_PROMPT}

Focus sur le suivi des interventions. Analyse:
- Historique des traitements par parcelle
- Respect des doses et conditions d'emploi
- Efficacité des interventions
- Conformité réglementaire
- Optimisation des calendriers
- Gestion des stocks d'intrants"""),
    ("human", """Suivi d'intervention demandé:
Type d'intervention: {intervention_type}
Période: {period}
Parcelles: {parcels}

{farm_context}

Question spécifique: {input}"""),
    ("ai", "{agent_scratchpad}")
])

# Cost Analysis Prompt
COST_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", f"""{FARM_DATA_SYSTEM_PROMPT}

Focus sur l'analyse des coûts. Évalue:
- Coûts directs (semences, engrais, produits phytosanitaires)
- Coûts indirects (main-d'œuvre, matériel, carburant)
- Coûts fixes (amortissements, assurances)
- Coûts variables par hectare
- Évolution des coûts dans le temps
- Comparaison avec références
- Optimisation des coûts"""),
    ("human", """Analyse de coûts demandée:
Période: {period}
Cultures: {crops}
Type de coûts: {cost_type}

{farm_context}

Question spécifique: {input}"""),
    ("ai", "{agent_scratchpad}")
])

# Trend Analysis Prompt
TREND_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", f"""{FARM_DATA_SYSTEM_PROMPT}

Focus sur l'analyse des tendances. Identifie:
- Évolutions des rendements dans le temps
- Tendances des coûts de production
- Variations saisonnières
- Impact des conditions météorologiques
- Efficacité des nouvelles pratiques
- Corrélations entre variables
- Prévisions et projections"""),
    ("human", """Analyse de tendances demandée:
Période d'analyse: {analysis_period}
Variables: {variables}
Granularité: {granularity}

{farm_context}

Question spécifique: {input}"""),
    ("ai", "{agent_scratchpad}")
])

# Export all prompts
__all__ = [
    "FARM_DATA_SYSTEM_PROMPT",
    "FARM_DATA_CHAT_PROMPT",
    "PARCEL_ANALYSIS_PROMPT",
    "PERFORMANCE_METRICS_PROMPT",
    "INTERVENTION_TRACKING_PROMPT",
    "COST_ANALYSIS_PROMPT",
    "TREND_ANALYSIS_PROMPT"
]
