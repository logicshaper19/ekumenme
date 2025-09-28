"""
Dynamic Few-Shot Examples System

This module provides dynamic few-shot example injection for each prompt type.
When a prompt is selected, relevant examples are dynamically injected to maximize
relevance and precision for the specific task at hand.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ExampleType(Enum):
    """Types of examples for different scenarios."""
    BASIC = "basic"
    COMPLEX = "complex"
    EDGE_CASE = "edge_case"
    ERROR_HANDLING = "error_handling"
    REGULATORY = "regulatory"
    SAFETY = "safety"

@dataclass
class FewShotExample:
    """Few-shot example with metadata."""
    prompt_type: str
    example_type: ExampleType
    user_query: str
    context: str
    expected_response: str
    reasoning: str
    confidence: float
    tags: List[str]
    created_at: datetime

@dataclass
class DynamicExampleConfig:
    """Configuration for dynamic example injection."""
    prompt_type: str
    max_examples: int
    example_types: List[ExampleType]
    priority_order: List[ExampleType]
    include_reasoning: bool
    include_confidence: bool

class DynamicFewShotManager:
    """
    Manager for dynamic few-shot example injection.
    
    Job: Provide relevant few-shot examples for each prompt type.
    Input: Prompt type, context, and configuration
    Output: Dynamically selected and formatted examples
    """
    
    def __init__(self):
        self.examples: Dict[str, List[FewShotExample]] = {}
        self.configs: Dict[str, DynamicExampleConfig] = {}
        self._initialize_example_library()
        self._initialize_configs()
    
    def _initialize_example_library(self):
        """Initialize the library of few-shot examples."""
        
        # Farm Data Examples
        self.examples["FARM_DATA_CHAT_PROMPT"] = [
            FewShotExample(
                prompt_type="FARM_DATA_CHAT_PROMPT",
                example_type=ExampleType.BASIC,
                user_query="Analyse les données de mon exploitation pour cette année",
                context="Exploitation de 150ha, blé, maïs, colza",
                expected_response="**Analyse de votre exploitation 2024:**\n\n**Surfaces:**\n- Blé: 60ha (40%)\n- Maïs: 45ha (30%)\n- Colza: 45ha (30%)\n\n**Rendements moyens:**\n- Blé: 75 q/ha\n- Maïs: 95 q/ha\n- Colza: 35 q/ha\n\n**Coûts totaux:** 45,000€\n**Marge brute:** 78,000€\n\n**Recommandations:**\n- Optimiser la fertilisation du blé\n- Diversifier les variétés de maïs",
                reasoning="Analyse globale avec métriques clés et recommandations",
                confidence=0.95,
                tags=["analyse", "exploitation", "métriques"],
                created_at=datetime.now()
            ),
            FewShotExample(
                prompt_type="FARM_DATA_CHAT_PROMPT",
                example_type=ExampleType.COMPLEX,
                user_query="Compare mes rendements avec les références régionales",
                context="Région Centre, exploitation conventionnelle, 3 ans de données",
                expected_response="**Comparaison rendements région Centre:**\n\n**Vos rendements vs références:**\n- Blé: 75 q/ha (réf: 72 q/ha) ✅ +4%\n- Maïs: 95 q/ha (réf: 88 q/ha) ✅ +8%\n- Colza: 35 q/ha (réf: 38 q/ha) ⚠️ -8%\n\n**Analyse:**\n- Excellente performance blé et maïs\n- Colza en dessous: vérifier variété et date semis\n\n**Actions:**\n- Maintenir pratiques blé/maïs\n- Optimiser colza: variété plus précoce",
                reasoning="Comparaison détaillée avec références et actions correctives",
                confidence=0.92,
                tags=["comparaison", "références", "optimisation"],
                created_at=datetime.now()
            )
        ]
        
        # Regulatory Examples
        self.examples["AMM_LOOKUP_PROMPT"] = [
            FewShotExample(
                prompt_type="AMM_LOOKUP_PROMPT",
                example_type=ExampleType.REGULATORY,
                user_query="Vérifier l'autorisation AMM du Roundup",
                context="Produit phytosanitaire, usage agricole",
                expected_response="**Vérification AMM Roundup:**\n\n**Statut:** ✅ Autorisé\n**Numéro AMM:** 2000233\n**Substance active:** Glyphosate 360 g/L\n\n**Usages autorisés:**\n- Désherbage total (ZNT: 5m)\n- Interculture (ZNT: 5m)\n- Jachère (ZNT: 5m)\n\n**⚠️ Restrictions importantes:**\n- Interdit sur culture en place\n- ZNT 5m obligatoire\n- Équipement de protection requis\n\n**Recommandation:** Produit autorisé pour usage agricole conforme",
                reasoning="Vérification complète AMM avec restrictions et recommandations",
                confidence=0.98,
                tags=["amm", "autorisation", "restrictions"],
                created_at=datetime.now()
            ),
            FewShotExample(
                prompt_type="AMM_LOOKUP_PROMPT",
                example_type=ExampleType.SAFETY,
                user_query="Le produit X est-il autorisé pour traiter mes pommes de terre?",
                context="Produit non spécifié, culture pommes de terre",
                expected_response="**⚠️ ATTENTION - Produit non identifié:**\n\n**Action requise:**\n1. Fournir le nom exact du produit\n2. Vérifier le numéro AMM\n3. Contrôler l'usage sur pommes de terre\n\n**Règles de sécurité:**\n- Ne jamais utiliser un produit non identifié\n- Vérifier AMM avant tout usage\n- Respecter les usages homologués\n\n**Recommandation:** Arrêter l'utilisation jusqu'à vérification complète",
                reasoning="Sécurité d'abord - refus d'utilisation sans vérification",
                confidence=1.0,
                tags=["sécurité", "vérification", "interdiction"],
                created_at=datetime.now()
            )
        ]
        
        # Weather Examples
        self.examples["WEATHER_FORECAST_PROMPT"] = [
            FewShotExample(
                prompt_type="WEATHER_FORECAST_PROMPT",
                example_type=ExampleType.BASIC,
                user_query="Quelles sont les prévisions météo pour la semaine?",
                context="Région Centre, période de traitement prévue",
                expected_response="**Prévisions météo - Semaine du 15 au 21 mars:**\n\n**Lundi 15:** ☀️ 12-18°C, vent 10 km/h - **FAVORABLE**\n**Mardi 16:** ☁️ 8-14°C, vent 15 km/h - **FAVORABLE**\n**Mercredi 17:** 🌧️ 6-12°C, pluie 5mm - **DÉFAVORABLE**\n**Jeudi 18:** ☀️ 10-16°C, vent 8 km/h - **FAVORABLE**\n**Vendredi 19:** ☀️ 14-20°C, vent 12 km/h - **FAVORABLE**\n\n**Recommandation:** Traitement optimal lundi, mardi, jeudi ou vendredi",
                reasoning="Prévisions détaillées avec recommandations d'intervention",
                confidence=0.90,
                tags=["prévisions", "intervention", "conditions"],
                created_at=datetime.now()
            ),
            FewShotExample(
                prompt_type="WEATHER_FORECAST_PROMPT",
                example_type=ExampleType.EDGE_CASE,
                user_query="Y a-t-il un risque de gel cette nuit?",
                context="Début avril, jeunes pousses de maïs",
                expected_response="**⚠️ ALERTE GEL - Nuit du 3 au 4 avril:**\n\n**Prévisions:**\n- Température minimale: -2°C\n- Gelée blanche probable\n- Vent faible (5 km/h)\n\n**Impact sur maïs:**\n- Risque de dégâts sur jeunes pousses\n- Stade critique: levée récente\n\n**Actions recommandées:**\n1. **Protection immédiate:** Couverture ou irrigation\n2. **Surveillance:** Contrôle matinal\n3. **Plan B:** Resemis si dégâts >30%\n\n**Suivi:** Nouvelle évaluation demain matin",
                reasoning="Alerte gel avec actions de protection spécifiques",
                confidence=0.95,
                tags=["gel", "alerte", "protection"],
                created_at=datetime.now()
            )
        ]
        
        # Crop Health Examples
        self.examples["DISEASE_DIAGNOSIS_PROMPT"] = [
            FewShotExample(
                prompt_type="DISEASE_DIAGNOSIS_PROMPT",
                example_type=ExampleType.BASIC,
                user_query="Mes blés ont des taches jaunes sur les feuilles",
                context="Blé tendre, stade épi 1cm, région Centre",
                expected_response="**Diagnostic - Taches jaunes sur blé:**\n\n**Symptômes observés:**\n- Taches jaunes sur feuilles\n- Stade: épi 1cm\n- Localisation: feuilles basses\n\n**Diagnostic probable:** Septoriose (Mycosphaerella graminicola)\n\n**Confirmation:**\n- Taches ovales avec centre gris\n- Bordure jaune caractéristique\n- Présence de pycnides noires\n\n**Traitement recommandé:**\n- Produit: Époxiconazole + Azoxystrobine\n- Dose: 1.5 L/ha\n- Conditions: temps sec, vent <20 km/h\n\n**Prévention:** Rotation, variétés résistantes",
                reasoning="Diagnostic structuré avec confirmation et traitement",
                confidence=0.88,
                tags=["diagnostic", "septoriose", "traitement"],
                created_at=datetime.now()
            ),
            FewShotExample(
                prompt_type="DISEASE_DIAGNOSIS_PROMPT",
                example_type=ExampleType.ERROR_HANDLING,
                user_query="Mes cultures ont un problème",
                context="Problème non spécifié",
                expected_response="**⚠️ Diagnostic impossible - Informations insuffisantes:**\n\n**Informations requises:**\n1. **Culture concernée:** Blé, maïs, colza, etc.\n2. **Symptômes précis:** Taches, décolorations, déformations\n3. **Localisation:** Feuilles, tiges, racines\n4. **Stade de développement:** Hauteur, stade phénologique\n5. **Conditions récentes:** Météo, traitements\n\n**Exemple de description:**\n'Blé tendre, taches ovales jaunes sur feuilles basses, stade épi 1cm, pluie récente'\n\n**Recommandation:** Fournir description détaillée pour diagnostic précis",
                reasoning="Demande d'informations complémentaires pour diagnostic",
                confidence=0.85,
                tags=["diagnostic", "informations", "aide"],
                created_at=datetime.now()
            )
        ]
        
        # Planning Examples
        self.examples["TASK_PLANNING_PROMPT"] = [
            FewShotExample(
                prompt_type="TASK_PLANNING_PROMPT",
                example_type=ExampleType.BASIC,
                user_query="Organiser mes travaux pour cette semaine",
                context="Exploitation 150ha, blé à traiter, semis maïs prévu",
                expected_response="**Planning hebdomadaire - Semaine du 15 mars:**\n\n**Lundi 15:**\n- Matin: Traitement blé (parcelle A, 25ha)\n- Après-midi: Préparation sol maïs (parcelle B)\n\n**Mardi 16:**\n- Matin: Traitement blé (parcelle C, 35ha)\n- Après-midi: Contrôle matériel semis\n\n**Mercredi 17:**\n- Journée: Semis maïs (parcelle B, 45ha)\n- Conditions météo favorables\n\n**Jeudi 18:**\n- Matin: Finition semis maïs\n- Après-midi: Entretien matériel\n\n**Vendredi 19:**\n- Contrôle levée maïs\n- Planification semaine suivante\n\n**Ressources:** 1 tracteur, 1 pulvérisateur, 1 semoir",
                reasoning="Planning détaillé avec ressources et contraintes",
                confidence=0.92,
                tags=["planning", "travaux", "ressources"],
                created_at=datetime.now()
            )
        ]
        
        # Sustainability Examples
        self.examples["CARBON_FOOTPRINT_PROMPT"] = [
            FewShotExample(
                prompt_type="CARBON_FOOTPRINT_PROMPT",
                example_type=ExampleType.BASIC,
                user_query="Calculer l'empreinte carbone de mon exploitation",
                context="Exploitation 150ha, blé-maïs-colza, conventionnel",
                expected_response="**Bilan carbone exploitation 2024:**\n\n**Émissions (t CO2eq/an):**\n- Carburant tracteurs: 12.5 t\n- Engrais azotés: 8.2 t\n- Produits phytosanitaires: 1.8 t\n- Semences: 0.5 t\n- **Total émissions: 23.0 t CO2eq**\n\n**Stockage carbone:**\n- Sols (matière organique): -2.1 t\n- Haies et bosquets: -0.8 t\n- **Total stockage: -2.9 t CO2eq**\n\n**Bilan net: +20.1 t CO2eq/an**\n\n**Comparaison:**\n- Référence régionale: +25.5 t CO2eq\n- **Performance: +21% meilleure**\n\n**Leviers d'amélioration:**\n- Réduction engrais azotés: -15%\n- Couverts végétaux: -10%\n- Optimisation carburant: -8%",
                reasoning="Bilan carbone complet avec comparaisons et améliorations",
                confidence=0.90,
                tags=["carbone", "bilan", "amélioration"],
                created_at=datetime.now()
            )
        ]
    
    def _initialize_configs(self):
        """Initialize configurations for dynamic example injection."""
        
        # Farm Data Config
        self.configs["FARM_DATA_CHAT_PROMPT"] = DynamicExampleConfig(
            prompt_type="FARM_DATA_CHAT_PROMPT",
            max_examples=2,
            example_types=[ExampleType.BASIC, ExampleType.COMPLEX],
            priority_order=[ExampleType.BASIC, ExampleType.COMPLEX],
            include_reasoning=True,
            include_confidence=True
        )
        
        # Regulatory Config
        self.configs["AMM_LOOKUP_PROMPT"] = DynamicExampleConfig(
            prompt_type="AMM_LOOKUP_PROMPT",
            max_examples=2,
            example_types=[ExampleType.REGULATORY, ExampleType.SAFETY],
            priority_order=[ExampleType.SAFETY, ExampleType.REGULATORY],
            include_reasoning=True,
            include_confidence=True
        )
        
        # Weather Config
        self.configs["WEATHER_FORECAST_PROMPT"] = DynamicExampleConfig(
            prompt_type="WEATHER_FORECAST_PROMPT",
            max_examples=2,
            example_types=[ExampleType.BASIC, ExampleType.EDGE_CASE],
            priority_order=[ExampleType.EDGE_CASE, ExampleType.BASIC],
            include_reasoning=True,
            include_confidence=True
        )
        
        # Crop Health Config
        self.configs["DISEASE_DIAGNOSIS_PROMPT"] = DynamicExampleConfig(
            prompt_type="DISEASE_DIAGNOSIS_PROMPT",
            max_examples=2,
            example_types=[ExampleType.BASIC, ExampleType.ERROR_HANDLING],
            priority_order=[ExampleType.ERROR_HANDLING, ExampleType.BASIC],
            include_reasoning=True,
            include_confidence=True
        )
        
        # Planning Config
        self.configs["TASK_PLANNING_PROMPT"] = DynamicExampleConfig(
            prompt_type="TASK_PLANNING_PROMPT",
            max_examples=1,
            example_types=[ExampleType.BASIC],
            priority_order=[ExampleType.BASIC],
            include_reasoning=True,
            include_confidence=True
        )
        
        # Sustainability Config
        self.configs["CARBON_FOOTPRINT_PROMPT"] = DynamicExampleConfig(
            prompt_type="CARBON_FOOTPRINT_PROMPT",
            max_examples=1,
            example_types=[ExampleType.BASIC],
            priority_order=[ExampleType.BASIC],
            include_reasoning=True,
            include_confidence=True
        )
    
    def get_dynamic_examples(self, prompt_type: str, context: str = "", 
                           user_query: str = "") -> str:
        """
        Get dynamically selected examples for a prompt type.
        
        Args:
            prompt_type: Type of prompt
            context: Additional context
            user_query: User query for relevance matching
            
        Returns:
            Formatted few-shot examples string
        """
        if prompt_type not in self.examples:
            return ""
        
        config = self.configs.get(prompt_type)
        if not config:
            return ""
        
        # Get available examples
        available_examples = self.examples[prompt_type]
        
        # Filter by example types in config
        filtered_examples = [
            ex for ex in available_examples 
            if ex.example_type in config.example_types
        ]
        
        # Sort by priority order
        type_priority = {t: i for i, t in enumerate(config.priority_order)}
        filtered_examples.sort(key=lambda x: type_priority.get(x.example_type, 999))
        
        # Select top examples
        selected_examples = filtered_examples[:config.max_examples]
        
        # Format examples
        formatted_examples = []
        for i, example in enumerate(selected_examples, 1):
            example_text = f"**Exemple {i}:**\n"
            example_text += f"**Question:** {example.user_query}\n"
            example_text += f"**Contexte:** {example.context}\n"
            example_text += f"**Réponse:**\n{example.expected_response}\n"
            
            if config.include_reasoning:
                example_text += f"**Raisonnement:** {example.reasoning}\n"
            
            if config.include_confidence:
                example_text += f"**Confiance:** {example.confidence:.2f}\n"
            
            formatted_examples.append(example_text)
        
        if formatted_examples:
            return "\n\n".join(formatted_examples)
        
        return ""
    
    def add_example(self, example: FewShotExample) -> bool:
        """Add a new few-shot example."""
        try:
            if example.prompt_type not in self.examples:
                self.examples[example.prompt_type] = []
            
            self.examples[example.prompt_type].append(example)
            logger.info(f"Added example for {example.prompt_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding example: {e}")
            return False
    
    def get_examples_for_prompt(self, prompt_type: str) -> List[FewShotExample]:
        """Get all examples for a specific prompt type."""
        return self.examples.get(prompt_type, [])
    
    def get_example_stats(self) -> Dict[str, Any]:
        """Get statistics about the example library."""
        stats = {}
        for prompt_type, examples in self.examples.items():
            stats[prompt_type] = {
                "total_examples": len(examples),
                "example_types": list(set(ex.example_type for ex in examples)),
                "avg_confidence": sum(ex.confidence for ex in examples) / len(examples) if examples else 0
            }
        return stats

# Global dynamic examples manager
dynamic_examples_manager = DynamicFewShotManager()

# Convenience functions
def get_dynamic_examples(prompt_type: str, context: str = "", user_query: str = "") -> str:
    """Get dynamically selected examples for a prompt type."""
    return dynamic_examples_manager.get_dynamic_examples(prompt_type, context, user_query)

def add_few_shot_example(prompt_type: str, example_type: ExampleType, 
                        user_query: str, context: str, expected_response: str,
                        reasoning: str, confidence: float, tags: List[str]) -> bool:
    """Add a new few-shot example."""
    example = FewShotExample(
        prompt_type=prompt_type,
        example_type=example_type,
        user_query=user_query,
        context=context,
        expected_response=expected_response,
        reasoning=reasoning,
        confidence=confidence,
        tags=tags,
        created_at=datetime.now()
    )
    return dynamic_examples_manager.add_example(example)

def get_example_stats() -> Dict[str, Any]:
    """Get statistics about the example library."""
    return dynamic_examples_manager.get_example_stats()

# Export all classes and functions
__all__ = [
    "DynamicFewShotManager",
    "FewShotExample",
    "DynamicExampleConfig",
    "ExampleType",
    "dynamic_examples_manager",
    "get_dynamic_examples",
    "add_few_shot_example",
    "get_example_stats"
]
