"""
Semantic Routing and Intent Classification

This module provides semantic search, embedding-based intent classification,
and LLM-based routing for intelligent prompt selection.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import json
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Optional semantic imports with graceful fallbacks
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None
    SEMANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Agricultural intent types."""
    # Farm Data Intents
    FARM_DATA_ANALYSIS = "farm_data_analysis"
    PARCEL_ANALYSIS = "parcel_analysis"
    PERFORMANCE_METRICS = "performance_metrics"
    INTERVENTION_TRACKING = "intervention_tracking"
    COST_ANALYSIS = "cost_analysis"
    TREND_ANALYSIS = "trend_analysis"
    
    # Regulatory Intents
    AMM_LOOKUP = "amm_lookup"
    USAGE_CONDITIONS = "usage_conditions"
    SAFETY_CLASSIFICATIONS = "safety_classifications"
    PRODUCT_SUBSTITUTION = "product_substitution"
    COMPLIANCE_CHECK = "compliance_check"
    ENVIRONMENTAL_REGULATIONS = "environmental_regulations"
    
    # Weather Intents
    WEATHER_FORECAST = "weather_forecast"
    INTERVENTION_WINDOW = "intervention_window"
    WEATHER_RISK_ANALYSIS = "weather_risk_analysis"
    IRRIGATION_PLANNING = "irrigation_planning"
    EVAPOTRANSPIRATION = "evapotranspiration"
    CLIMATE_ADAPTATION = "climate_adaptation"
    
    # Crop Health Intents
    DISEASE_DIAGNOSIS = "disease_diagnosis"
    PEST_IDENTIFICATION = "pest_identification"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    TREATMENT_PLAN = "treatment_plan"
    RESISTANCE_MANAGEMENT = "resistance_management"
    BIOLOGICAL_CONTROL = "biological_control"
    
    # Planning Intents
    TASK_PLANNING = "task_planning"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SEASONAL_PLANNING = "seasonal_planning"
    WEATHER_DEPENDENT_PLANNING = "weather_dependent_planning"
    COST_OPTIMIZATION = "cost_optimization"
    EMERGENCY_PLANNING = "emergency_planning"
    
    # Sustainability Intents
    CARBON_FOOTPRINT = "carbon_footprint"
    BIODIVERSITY_ASSESSMENT = "biodiversity_assessment"
    SOIL_HEALTH = "soil_health"
    WATER_MANAGEMENT = "water_management"
    ENERGY_EFFICIENCY = "energy_efficiency"
    CERTIFICATION_SUPPORT = "certification_support"

@dataclass
class IntentExample:
    """Example query for intent classification."""
    intent: IntentType
    query: str
    context: str
    expected_prompt: str
    confidence_threshold: float = 0.8

@dataclass
class IntentClassification:
    """Result of intent classification."""
    intent: IntentType
    confidence: float
    selected_prompt: str
    reasoning: str
    alternative_intents: List[Tuple[IntentType, float]]

class SemanticIntentClassifier:
    """
    Semantic intent classifier using embeddings and LLM-based routing.
    
    Job: Classify user queries semantically and select appropriate prompts.
    Input: User query and context
    Output: Intent classification and prompt selection
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = None
        self.intent_examples: List[IntentExample] = []
        self.intent_embeddings: Dict[IntentType, np.ndarray] = {}
        
        if SEMANTIC_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
        
        self._initialize_intent_examples()
        self._compute_intent_embeddings()
    
    def _initialize_intent_examples(self):
        """Initialize intent examples for classification."""
        self.intent_examples = [
            # Farm Data Examples
            IntentExample(
                intent=IntentType.FARM_DATA_ANALYSIS,
                query="Analyse les données de mon exploitation pour cette année",
                context="L'agriculteur veut une analyse globale de ses données",
                expected_prompt="FARM_DATA_CHAT_PROMPT"
            ),
            IntentExample(
                intent=IntentType.PARCEL_ANALYSIS,
                query="Comment analyser la performance de ma parcelle de blé?",
                context="Analyse spécifique d'une parcelle",
                expected_prompt="PARCEL_ANALYSIS_PROMPT"
            ),
            IntentExample(
                intent=IntentType.PERFORMANCE_METRICS,
                query="Quels sont mes rendements par hectare cette saison?",
                context="Calcul de métriques de performance",
                expected_prompt="PERFORMANCE_METRICS_PROMPT"
            ),
            
            # Regulatory Examples
            IntentExample(
                intent=IntentType.AMM_LOOKUP,
                query="Vérifier l'autorisation AMM du Roundup",
                context="Vérification réglementaire d'un produit",
                expected_prompt="AMM_LOOKUP_PROMPT"
            ),
            IntentExample(
                intent=IntentType.USAGE_CONDITIONS,
                query="Quelles sont les conditions d'emploi du glyphosate?",
                context="Conditions d'utilisation d'un produit",
                expected_prompt="USAGE_CONDITIONS_PROMPT"
            ),
            IntentExample(
                intent=IntentType.COMPLIANCE_CHECK,
                query="Suis-je en conformité avec mes traitements?",
                context="Vérification de conformité",
                expected_prompt="COMPLIANCE_CHECK_PROMPT"
            ),
            
            # Weather Examples
            IntentExample(
                intent=IntentType.WEATHER_FORECAST,
                query="Quelles sont les prévisions météo pour la semaine?",
                context="Demande de prévisions météorologiques",
                expected_prompt="WEATHER_FORECAST_PROMPT"
            ),
            IntentExample(
                intent=IntentType.INTERVENTION_WINDOW,
                query="Quand puis-je traiter mes céréales?",
                context="Fenêtre d'intervention météo",
                expected_prompt="INTERVENTION_WINDOW_PROMPT"
            ),
            IntentExample(
                intent=IntentType.IRRIGATION_PLANNING,
                query="Quand dois-je irriguer mes cultures?",
                context="Planification d'irrigation",
                expected_prompt="IRRIGATION_PLANNING_PROMPT"
            ),
            
            # Crop Health Examples
            IntentExample(
                intent=IntentType.DISEASE_DIAGNOSIS,
                query="Mes blés ont des taches jaunes, qu'est-ce que c'est?",
                context="Diagnostic de maladie",
                expected_prompt="DISEASE_DIAGNOSIS_PROMPT"
            ),
            IntentExample(
                intent=IntentType.PEST_IDENTIFICATION,
                query="J'ai des insectes sur mes pommes de terre",
                context="Identification de ravageurs",
                expected_prompt="PEST_IDENTIFICATION_PROMPT"
            ),
            IntentExample(
                intent=IntentType.TREATMENT_PLAN,
                query="Quel traitement pour lutter contre la septoriose?",
                context="Plan de traitement",
                expected_prompt="TREATMENT_PLAN_PROMPT"
            ),
            
            # Planning Examples
            IntentExample(
                intent=IntentType.TASK_PLANNING,
                query="Organiser mes travaux pour cette semaine",
                context="Planification de tâches",
                expected_prompt="TASK_PLANNING_PROMPT"
            ),
            IntentExample(
                intent=IntentType.RESOURCE_OPTIMIZATION,
                query="Optimiser l'utilisation de mon matériel",
                context="Optimisation des ressources",
                expected_prompt="RESOURCE_OPTIMIZATION_PROMPT"
            ),
            IntentExample(
                intent=IntentType.EMERGENCY_PLANNING,
                query="Réorganiser mes travaux à cause de la pluie",
                context="Planification d'urgence",
                expected_prompt="EMERGENCY_PLANNING_PROMPT"
            ),
            
            # Sustainability Examples
            IntentExample(
                intent=IntentType.CARBON_FOOTPRINT,
                query="Calculer l'empreinte carbone de mon exploitation",
                context="Analyse carbone",
                expected_prompt="CARBON_FOOTPRINT_PROMPT"
            ),
            IntentExample(
                intent=IntentType.SOIL_HEALTH,
                query="Évaluer la santé de mes sols",
                context="Analyse de santé des sols",
                expected_prompt="SOIL_HEALTH_PROMPT"
            ),
            IntentExample(
                intent=IntentType.CERTIFICATION_SUPPORT,
                query="Préparer ma certification HVE",
                context="Support à la certification",
                expected_prompt="CERTIFICATION_SUPPORT_PROMPT"
            )
        ]
    
    def _compute_intent_embeddings(self):
        """Compute embeddings for intent examples."""
        if not self.embedding_model:
            logger.warning("No embedding model available, using fallback classification")
            return
        
        try:
            for example in self.intent_examples:
                # Combine query and context for better representation
                text = f"{example.query} {example.context}"
                embedding = self.embedding_model.encode([text])[0]
                
                if example.intent not in self.intent_embeddings:
                    self.intent_embeddings[example.intent] = []
                
                self.intent_embeddings[example.intent].append(embedding)
            
            # Average embeddings per intent
            for intent in self.intent_embeddings:
                embeddings = np.array(self.intent_embeddings[intent])
                self.intent_embeddings[intent] = np.mean(embeddings, axis=0)
            
            logger.info(f"Computed embeddings for {len(self.intent_embeddings)} intents")
            
        except Exception as e:
            logger.error(f"Error computing intent embeddings: {e}")
            self.intent_embeddings = {}
    
    def classify_intent_semantic(self, query: str, context: str = "") -> IntentClassification:
        """
        Classify intent using semantic similarity.
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Intent classification result
        """
        if not self.embedding_model or not self.intent_embeddings:
            return self._fallback_classification(query, context)
        
        try:
            # Encode the query
            query_text = f"{query} {context}"
            query_embedding = self.embedding_model.encode([query_text])[0]
            
            # Compute similarities
            similarities = {}
            for intent, intent_embedding in self.intent_embeddings.items():
                similarity = cosine_similarity([query_embedding], [intent_embedding])[0][0]
                similarities[intent] = float(similarity)
            
            # Sort by similarity
            sorted_intents = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
            
            # Get best match
            best_intent, best_confidence = sorted_intents[0]
            
            # Find corresponding prompt
            selected_prompt = self._get_prompt_for_intent(best_intent)
            
            # Generate reasoning
            reasoning = f"Semantic similarity: {best_confidence:.3f} with {best_intent.value}"
            
            return IntentClassification(
                intent=best_intent,
                confidence=best_confidence,
                selected_prompt=selected_prompt,
                reasoning=reasoning,
                alternative_intents=sorted_intents[1:4]  # Top 3 alternatives
            )
            
        except Exception as e:
            logger.error(f"Error in semantic classification: {e}")
            return self._fallback_classification(query, context)
    
    def classify_intent_llm(self, query: str, context: str = "") -> IntentClassification:
        """
        Classify intent using LLM-based routing.
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Intent classification result
        """
        # This would use a fast, cheap LLM for classification
        # For now, we'll use a rule-based approach as fallback
        return self._llm_based_classification(query, context)
    
    def _llm_based_classification(self, query: str, context: str = "") -> IntentClassification:
        """LLM-based classification using pattern matching."""
        query_lower = query.lower()
        
        # Define classification patterns
        patterns = {
            IntentType.AMM_LOOKUP: ["amm", "autorisation", "roundup", "glyphosate", "vérifier"],
            IntentType.WEATHER_FORECAST: ["météo", "prévision", "temps", "pluie", "vent"],
            IntentType.DISEASE_DIAGNOSIS: ["maladie", "tache", "symptôme", "diagnostic"],
            IntentType.TASK_PLANNING: ["planifier", "organiser", "travaux", "planning"],
            IntentType.CARBON_FOOTPRINT: ["carbone", "empreinte", "co2", "émission"],
            IntentType.PERFORMANCE_METRICS: ["rendement", "performance", "métrique", "analyse"]
        }
        
        # Find best match
        best_intent = IntentType.FARM_DATA_ANALYSIS  # Default
        best_score = 0
        
        for intent, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        confidence = min(0.9, 0.5 + (best_score * 0.1))
        selected_prompt = self._get_prompt_for_intent(best_intent)
        
        return IntentClassification(
            intent=best_intent,
            confidence=confidence,
            selected_prompt=selected_prompt,
            reasoning=f"LLM-based classification with {best_score} keyword matches",
            alternative_intents=[]
        )
    
    def _fallback_classification(self, query: str, context: str = "") -> IntentClassification:
        """Fallback classification when semantic methods fail."""
        return IntentClassification(
            intent=IntentType.FARM_DATA_ANALYSIS,
            confidence=0.5,
            selected_prompt="FARM_DATA_CHAT_PROMPT",
            reasoning="Fallback classification - defaulting to farm data analysis",
            alternative_intents=[]
        )
    
    def _get_prompt_for_intent(self, intent: IntentType) -> str:
        """Get the appropriate prompt for an intent."""
        prompt_mapping = {
            # Farm Data
            IntentType.FARM_DATA_ANALYSIS: "FARM_DATA_CHAT_PROMPT",
            IntentType.PARCEL_ANALYSIS: "PARCEL_ANALYSIS_PROMPT",
            IntentType.PERFORMANCE_METRICS: "PERFORMANCE_METRICS_PROMPT",
            IntentType.INTERVENTION_TRACKING: "INTERVENTION_TRACKING_PROMPT",
            IntentType.COST_ANALYSIS: "COST_ANALYSIS_PROMPT",
            IntentType.TREND_ANALYSIS: "TREND_ANALYSIS_PROMPT",
            
            # Regulatory
            IntentType.AMM_LOOKUP: "AMM_LOOKUP_PROMPT",
            IntentType.USAGE_CONDITIONS: "USAGE_CONDITIONS_PROMPT",
            IntentType.SAFETY_CLASSIFICATIONS: "SAFETY_CLASSIFICATIONS_PROMPT",
            IntentType.PRODUCT_SUBSTITUTION: "PRODUCT_SUBSTITUTION_PROMPT",
            IntentType.COMPLIANCE_CHECK: "COMPLIANCE_CHECK_PROMPT",
            IntentType.ENVIRONMENTAL_REGULATIONS: "ENVIRONMENTAL_REGULATIONS_PROMPT",
            
            # Weather
            IntentType.WEATHER_FORECAST: "WEATHER_FORECAST_PROMPT",
            IntentType.INTERVENTION_WINDOW: "INTERVENTION_WINDOW_PROMPT",
            IntentType.WEATHER_RISK_ANALYSIS: "WEATHER_RISK_ANALYSIS_PROMPT",
            IntentType.IRRIGATION_PLANNING: "IRRIGATION_PLANNING_PROMPT",
            IntentType.EVAPOTRANSPIRATION: "EVAPOTRANSPIRATION_PROMPT",
            IntentType.CLIMATE_ADAPTATION: "CLIMATE_ADAPTATION_PROMPT",
            
            # Crop Health
            IntentType.DISEASE_DIAGNOSIS: "DISEASE_DIAGNOSIS_PROMPT",
            IntentType.PEST_IDENTIFICATION: "PEST_IDENTIFICATION_PROMPT",
            IntentType.NUTRIENT_DEFICIENCY: "NUTRIENT_DEFICIENCY_PROMPT",
            IntentType.TREATMENT_PLAN: "TREATMENT_PLAN_PROMPT",
            IntentType.RESISTANCE_MANAGEMENT: "RESISTANCE_MANAGEMENT_PROMPT",
            IntentType.BIOLOGICAL_CONTROL: "BIOLOGICAL_CONTROL_PROMPT",
            
            # Planning
            IntentType.TASK_PLANNING: "TASK_PLANNING_PROMPT",
            IntentType.RESOURCE_OPTIMIZATION: "RESOURCE_OPTIMIZATION_PROMPT",
            IntentType.SEASONAL_PLANNING: "SEASONAL_PLANNING_PROMPT",
            IntentType.WEATHER_DEPENDENT_PLANNING: "WEATHER_DEPENDENT_PLANNING_PROMPT",
            IntentType.COST_OPTIMIZATION: "COST_OPTIMIZATION_PROMPT",
            IntentType.EMERGENCY_PLANNING: "EMERGENCY_PLANNING_PROMPT",
            
            # Sustainability
            IntentType.CARBON_FOOTPRINT: "CARBON_FOOTPRINT_PROMPT",
            IntentType.BIODIVERSITY_ASSESSMENT: "BIODIVERSITY_ASSESSMENT_PROMPT",
            IntentType.SOIL_HEALTH: "SOIL_HEALTH_PROMPT",
            IntentType.WATER_MANAGEMENT: "WATER_MANAGEMENT_PROMPT",
            IntentType.ENERGY_EFFICIENCY: "ENERGY_EFFICIENCY_PROMPT",
            IntentType.CERTIFICATION_SUPPORT: "CERTIFICATION_SUPPORT_PROMPT"
        }
        
        return prompt_mapping.get(intent, "FARM_DATA_CHAT_PROMPT")
    
    def get_intent_examples(self, intent: IntentType = None) -> List[IntentExample]:
        """Get examples for a specific intent or all intents."""
        if intent:
            return [ex for ex in self.intent_examples if ex.intent == intent]
        return self.intent_examples.copy()
    
    def add_intent_example(self, example: IntentExample) -> bool:
        """Add a new intent example."""
        try:
            self.intent_examples.append(example)
            if self.embedding_model:
                self._compute_intent_embeddings()
            return True
        except Exception as e:
            logger.error(f"Error adding intent example: {e}")
            return False

# Global semantic classifier instance
semantic_classifier = SemanticIntentClassifier()

# Convenience functions
def classify_intent(query: str, context: str = "", method: str = "semantic") -> IntentClassification:
    """Classify user intent using specified method."""
    if method == "semantic":
        return semantic_classifier.classify_intent_semantic(query, context)
    elif method == "llm":
        return semantic_classifier.classify_intent_llm(query, context)
    else:
        return semantic_classifier._fallback_classification(query, context)

def get_prompt_for_query(query: str, context: str = "") -> str:
    """Get the appropriate prompt for a user query."""
    classification = classify_intent(query, context)
    return classification.selected_prompt

# Export all classes and functions
__all__ = [
    "SemanticIntentClassifier",
    "IntentType",
    "IntentExample",
    "IntentClassification",
    "semantic_classifier",
    "classify_intent",
    "get_prompt_for_query"
]
