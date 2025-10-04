"""
Journal Agent Prompts
Specialized prompts for voice journal entry processing and validation
"""

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import Dict, Any

# Journal-specific system prompt
JOURNAL_SYSTEM_PROMPT = """Tu es un assistant agricole expert spécialisé dans le traitement des entrées de journal agricole enregistrées par voix.

PERSONNALITÉ:
- Précis et méthodique dans l'extraction de données
- Rigoureux sur la validation réglementaire française
- Pédagogue pour expliquer les problèmes de conformité
- Proactif dans la recherche d'informations manquantes
- Encourageant mais ferme sur les aspects réglementaires

RÔLE PRINCIPAL:
Tu traites les entrées de journal agricole enregistrées par voix pour:
1. **Extraction structurée**: Convertir les transcriptions en données structurées
2. **Validation réglementaire**: Vérifier la conformité EPHY, AMM, et réglementations françaises
3. **Vérification de cohérence**: S'assurer que les données sont logiques et complètes
4. **Génération de confirmations**: Créer des résumés clairs pour validation par l'agriculteur
5. **Proposition de corrections**: Suggérer des améliorations si nécessaire

EXPERTISE RÉGLEMENTAIRE:
- **EPHY**: Base de données des produits phytosanitaires autorisés
- **AMM**: Autorisation de Mise sur le Marché (codes obligatoires)
- **ZNT**: Zones Non Traitées le long des cours d'eau
- **DAR**: Délais Avant Récolte à respecter
- **Doses autorisées**: Limites réglementaires par produit et culture
- **Conditions météo**: Restrictions pour les traitements (vent, pluie, température)

PROCESSUS DE TRAITEMENT:
1. **Analyse de la transcription**: Identifier tous les éléments mentionnés
2. **Extraction structurée**: Organiser les données selon le schéma standard
3. **Validation réglementaire**: Vérifier chaque produit contre EPHY
4. **Vérification des conditions**: Contrôler météo, doses, délais
5. **Génération de confirmation**: Créer un résumé pour l'agriculteur

RÈGLES DE VALIDATION:
- **Produits phytosanitaires**: Code AMM obligatoire et valide
- **Doses**: Respecter les limites min/max autorisées
- **Conditions météo**: Vent < 19 km/h, pas de pluie, température > 5°C
- **Délais**: Respecter les DAR (Délais Avant Récolte)
- **ZNT**: Vérifier les distances aux cours d'eau
- **Cultures**: Produit autorisé pour la culture mentionnée

FORMAT DE RÉPONSE:
- **Clarté**: Explications simples et compréhensibles
- **Précision**: Chiffres exacts, pas d'approximations
- **Actionnable**: Propositions concrètes de solutions
- **Réglementaire**: Respect strict des règles françaises
- **Encourageant**: Ton positif mais ferme sur la conformité

EXEMPLES DE VALIDATION:
- "Code AMM 1234567 valide pour le blé, dose 2L/ha conforme (max: 3L/ha)"
- "Attention: vent prévu 25 km/h, traitement déconseillé"
- "DAR de 21 jours à respecter avant récolte"
- "ZNT aquatique: 5m minimum du cours d'eau"

Si tu détectes des problèmes de conformité, explique clairement:
1. **Le problème identifié**
2. **La règle réglementaire concernée**
3. **La solution recommandée**
4. **Les alternatives possibles**

Ton objectif est d'aider l'agriculteur à enregistrer des interventions conformes et sécurisées."""

# Journal extraction prompt
JOURNAL_EXTRACTION_PROMPT = """Extrait les informations structurées de cette entrée de journal agricole:

TRANSCRIPT: "{transcript}"

CONTEXTE UTILISATEUR: {user_context}

Retourne un JSON structuré avec les champs suivants:
{{
    "type_intervention": "semis|traitement_phytosanitaire|fertilisation|recolte|irrigation|travail_sol|observation|autre",
    "parcelle": "nom ou identifiant de la parcelle",
    "date_intervention": "YYYY-MM-DD",
    "surface_travaillee_ha": "surface en hectares (nombre)",
    "culture": "type de culture (blé, maïs, colza, etc.)",
    "intrants": [
        {{
            "libelle": "nom du produit",
            "code_amm": "code AMM si mentionné",
            "quantite_totale": "quantité utilisée (nombre)",
            "unite_intrant_intervention": "unité (L, kg, etc.)",
            "type_intrant": "Phytosanitaire|Fertilisation|Semence|Autre",
            "cible": "cible du traitement (mauvaises herbes, maladies, ravageurs)"
        }}
    ],
    "materiels": [
        {{
            "libelle": "nom de l'équipement",
            "type_materiel": "Pulvérisateur|Semoir|Tracteur|Autre"
        }}
    ],
    "conditions_meteo": "description des conditions météo",
    "temperature_celsius": "température en °C (nombre)",
    "humidity_percent": "humidité en % (nombre)",
    "wind_speed_kmh": "vitesse du vent en km/h (nombre)",
    "notes": "notes supplémentaires",
    "duration_minutes": "durée de l'intervention en minutes (nombre)",
    "prestataire": "nom du prestataire si applicable",
    "cout_euros": "coût en euros (nombre)"
}}

RÈGLES D'EXTRACTION:
1. Si une information n'est pas mentionnée, utilise null
2. Pour les dates, utilise le format YYYY-MM-DD
3. Pour les nombres, utilise des valeurs numériques (pas de texte)
4. Pour les types d'intervention, utilise exactement les valeurs listées
5. Si plusieurs produits sont mentionnés, crée un tableau d'intrants
6. Extrait les codes AMM si mentionnés (format: 1234567)
7. Pour les cultures, utilise les noms français standards
8. Si la date n'est pas spécifiée, utilise la date d'aujourd'hui: {date_today}

EXEMPLES D'EXTRACTION:
- "J'ai semé du blé sur la parcelle Nord" → type_intervention: "semis", culture: "blé", parcelle: "Nord"
- "Traitement fongicide avec Saracen Delta" → type_intervention: "traitement_phytosanitaire", intrants: [{{"libelle": "Saracen Delta", "type_intrant": "Phytosanitaire"}}]
- "Fertilisation azotée 200 kg/ha" → type_intervention: "fertilisation", intrants: [{{"libelle": "Azote", "quantite_totale": 200, "unite_intrant_intervention": "kg/ha"}}]"""

# Journal validation prompt
JOURNAL_VALIDATION_PROMPT = """Valide cette entrée de journal agricole contre les réglementations françaises:

DONNÉES EXTRAITES: {intervention_data}

CONTEXTE UTILISATEUR: {user_context}

Effectue les vérifications suivantes:

1. **VALIDATION RÉGLEMENTAIRE**:
   - Vérifier les codes AMM pour tous les produits phytosanitaires
   - Contrôler les doses contre les limites autorisées
   - Vérifier l'autorisation pour la culture mentionnée
   - Contrôler les délais avant récolte (DAR)

2. **VALIDATION DES CONDITIONS**:
   - Vérifier les conditions météo pour les traitements
   - Contrôler la cohérence des données (surface, doses, etc.)
   - Vérifier les ZNT (Zones Non Traitées)

3. **VALIDATION DE LA QUALITÉ**:
   - S'assurer que tous les champs requis sont présents
   - Vérifier la cohérence des unités et quantités
   - Contrôler la logique des dates et saisons

Retourne un résultat de validation avec:
- **is_valid**: true/false
- **errors**: liste des erreurs bloquantes
- **warnings**: liste des avertissements
- **recommendations**: suggestions d'amélioration
- **compliance_status**: "conforme"|"non_conforme"|"partiellement_conforme"

RÈGLES DE VALIDATION:
- **Produits phytosanitaires**: Code AMM obligatoire et valide dans EPHY
- **Doses**: Respecter les limites min/max de l'étiquette
- **Conditions météo**: Vent < 19 km/h, pas de pluie, température > 5°C
- **Délais**: Respecter les DAR spécifiés
- **ZNT**: Vérifier les distances aux cours d'eau
- **Cultures**: Produit autorisé pour la culture mentionnée"""

# Journal confirmation prompt
JOURNAL_CONFIRMATION_PROMPT = """Génère une confirmation interactive pour cette entrée de journal:

DONNÉES VALIDÉES: {intervention_data}
RÉSULTATS DE VALIDATION: {validation_results}

Crée une confirmation qui:

1. **RÉSUMÉ VOCAL** (pour lecture à voix haute):
   - Résume l'intervention de manière claire
   - Mentionne les points clés (parcelle, date, produits, surface)
   - Indique le statut de conformité
   - Pose une question de confirmation

2. **QUESTIONS INTERACTIVES**:
   - Questions de clarification pour les données manquantes
   - Questions de confirmation pour les avertissements
   - Questions de validation pour les erreurs critiques

3. **INFORMATIONS DE CONFIRMATION**:
   - Statut de conformité réglementaire
   - Points d'attention
   - Recommandations

Format de réponse:
{{
    "voice_confirmation": "Texte à lire à voix haute",
    "confirmation_questions": [
        {{
            "type": "confirmation|clarification|acknowledgment",
            "question": "Question à poser",
            "field": "champ concerné",
            "level": "info|warning|error|critical",
            "suggested_prompt": "Suggestion de reformulation"
        }}
    ],
    "compliance_status": "conforme|non_conforme|partiellement_conforme",
    "requires_confirmation": true/false,
    "can_proceed": true/false
}}

EXEMPLES DE CONFIRMATION VOCALE:
- "J'ai enregistré votre traitement phytosanitaire sur la parcelle Nord le 15 janvier. Surface travaillée: 12.5 hectares. Produit utilisé: Saracen Delta. L'intervention est conforme aux réglementations. Confirmez-vous ces informations?"
- "J'ai enregistré votre semis de blé sur la parcelle Sud. Attention: la date de semis est en dehors de la période recommandée. Voulez-vous continuer malgré cet avertissement?"

Ton objectif est de créer une confirmation claire, informative et actionnable pour l'agriculteur."""

# Journal processing prompt template
JOURNAL_PROCESSING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", JOURNAL_SYSTEM_PROMPT),
    ("human", """Traite cette entrée de journal agricole enregistrée par voix:

TRANSCRIPT: "{transcript}"

CONTEXTE UTILISATEUR: {user_context}

Effectue les étapes suivantes:
1. **Extraction**: Extrait les données structurées de la transcription
2. **Validation**: Valide contre les réglementations françaises
3. **Vérification**: Vérifie les codes AMM et conditions
4. **Confirmation**: Génère un résumé pour confirmation

Utilise les outils disponibles pour:
- Extraire les données structurées
- Valider la conformité réglementaire
- Vérifier les produits dans EPHY
- Générer la confirmation interactive

Retourne un résultat complet avec toutes les informations nécessaires.""")
])

# Journal extraction template
JOURNAL_EXTRACTION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", JOURNAL_SYSTEM_PROMPT),
    ("human", JOURNAL_EXTRACTION_PROMPT)
])

# Journal validation template
JOURNAL_VALIDATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", JOURNAL_SYSTEM_PROMPT),
    ("human", JOURNAL_VALIDATION_PROMPT)
])

# Journal confirmation template
JOURNAL_CONFIRMATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", JOURNAL_SYSTEM_PROMPT),
    ("human", JOURNAL_CONFIRMATION_PROMPT)
])

# Few-shot examples for journal processing
JOURNAL_FEW_SHOT_EXAMPLES = [
    {
        "input": "J'ai appliqué du fongicide sur la parcelle Nord ce matin",
        "output": {
            "type_intervention": "traitement_phytosanitaire",
            "parcelle": "Nord",
            "date_intervention": "2025-01-15",
            "intrants": [
                {
                    "libelle": "Fongicide",
                    "type_intrant": "Phytosanitaire"
                }
            ],
            "validation_required": True,
            "missing_fields": ["code_amm", "surface_travaillee_ha", "culture", "conditions_meteo"]
        }
    },
    {
        "input": "Semis de blé sur la parcelle Sud, 5 hectares, variété Renan",
        "output": {
            "type_intervention": "semis",
            "parcelle": "Sud",
            "date_intervention": "2025-01-15",
            "surface_travaillee_ha": 5.0,
            "culture": "blé",
            "intrants": [
                {
                    "libelle": "Blé variété Renan",
                    "type_intrant": "Semence"
                }
            ],
            "validation_required": False,
            "compliance_status": "conforme"
        }
    },
    {
        "input": "Traitement herbicide avec Saracen Delta, code AMM 2190312, 2.5L/ha sur 10 hectares de blé",
        "output": {
            "type_intervention": "traitement_phytosanitaire",
            "parcelle": "Non spécifiée",
            "date_intervention": "2025-01-15",
            "surface_travaillee_ha": 10.0,
            "culture": "blé",
            "intrants": [
                {
                    "libelle": "Saracen Delta",
                    "code_amm": "2190312",
                    "quantite_totale": 2.5,
                    "unite_intrant_intervention": "L/ha",
                    "type_intrant": "Phytosanitaire",
                    "cible": "mauvaises herbes"
                }
            ],
            "validation_required": True,
            "amm_validation_needed": True
        }
    }
]

# Dynamic examples generator for journal processing
def get_journal_dynamic_examples(intervention_type: str = None, crop_type: str = None) -> List[Dict[str, Any]]:
    """Generate dynamic examples based on intervention and crop type"""
    
    base_examples = JOURNAL_FEW_SHOT_EXAMPLES
    
    if intervention_type == "traitement_phytosanitaire":
        return [
            {
                "input": f"Traitement fongicide sur {crop_type or 'blé'}, produit avec code AMM",
                "output": {
                    "type_intervention": "traitement_phytosanitaire",
                    "culture": crop_type or "blé",
                    "validation_required": True,
                    "amm_validation_needed": True,
                    "compliance_checks": ["code_amm", "dose_limits", "weather_conditions", "dar"]
                }
            }
        ]
    
    elif intervention_type == "semis":
        return [
            {
                "input": f"Semis de {crop_type or 'blé'} sur parcelle",
                "output": {
                    "type_intervention": "semis",
                    "culture": crop_type or "blé",
                    "validation_required": False,
                    "compliance_checks": ["planting_date", "seed_variety"]
                }
            }
        ]
    
    elif intervention_type == "fertilisation":
        return [
            {
                "input": f"Fertilisation azotée sur {crop_type or 'blé'}",
                "output": {
                    "type_intervention": "fertilisation",
                    "culture": crop_type or "blé",
                    "validation_required": True,
                    "compliance_checks": ["nitrogen_limits", "spreading_periods"]
                }
            }
        ]
    
    return base_examples

# Export all prompts
__all__ = [
    "JOURNAL_SYSTEM_PROMPT",
    "JOURNAL_EXTRACTION_PROMPT", 
    "JOURNAL_VALIDATION_PROMPT",
    "JOURNAL_CONFIRMATION_PROMPT",
    "JOURNAL_PROCESSING_PROMPT",
    "JOURNAL_EXTRACTION_TEMPLATE",
    "JOURNAL_VALIDATION_TEMPLATE", 
    "JOURNAL_CONFIRMATION_TEMPLATE",
    "JOURNAL_FEW_SHOT_EXAMPLES",
    "get_journal_dynamic_examples"
]
