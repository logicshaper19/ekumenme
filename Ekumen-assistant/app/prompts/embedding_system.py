"""
Embedding-Based Prompt Matching System

This module provides embedding-based prompt matching, semantic search,
and intelligent prompt selection using vector similarity.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import pickle
import os

# Optional semantic imports with graceful fallbacks
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None
    TfidfVectorizer = None
    SEMANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class PromptEmbedding:
    """Embedding representation of a prompt."""
    prompt_name: str
    agent_type: str
    prompt_type: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class PromptMatch:
    """Result of prompt matching."""
    prompt_name: str
    similarity_score: float
    agent_type: str
    prompt_type: str
    reasoning: str
    metadata: Dict[str, Any]

class EmbeddingPromptMatcher:
    """
    Embedding-based prompt matching system.
    
    Job: Match user queries to appropriate prompts using semantic similarity.
    Input: User query and context
    Output: Best matching prompt with similarity score
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = None
        self.prompt_embeddings: Dict[str, PromptEmbedding] = {}
        self.tfidf_vectorizer = None
        self.tfidf_embeddings = None
        self.prompt_descriptions = []
        
        if SEMANTIC_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(model_name)
                self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
        
        self._initialize_prompt_embeddings()
    
    def _initialize_prompt_embeddings(self):
        """Initialize embeddings for all available prompts."""
        # Define prompt descriptions for embedding
        prompt_descriptions = {
            # Farm Data Prompts
            "FARM_DATA_CHAT_PROMPT": "Analyse générale des données d'exploitation agricole, parcelles, interventions, bilans de performance",
            "PARCEL_ANALYSIS_PROMPT": "Analyse spécifique d'une parcelle agricole, surface, cultures, rotations, historique, performance",
            "PERFORMANCE_METRICS_PROMPT": "Calcul et analyse des métriques de performance, rendements, coûts, marges par parcelle",
            "INTERVENTION_TRACKING_PROMPT": "Suivi des interventions agricoles, traitements, doses, dates, conformité",
            "COST_ANALYSIS_PROMPT": "Analyse des coûts de production, intrants, main-d'œuvre, matériel, optimisation",
            "TREND_ANALYSIS_PROMPT": "Analyse des tendances, évolutions, comparaisons temporelles, projections",
            
            # Regulatory Prompts
            "REGULATORY_CHAT_PROMPT": "Conseil réglementaire général, autorisations, conformité, sécurité des produits phytosanitaires",
            "AMM_LOOKUP_PROMPT": "Vérification des autorisations AMM, numéros d'autorisation, statuts des produits",
            "USAGE_CONDITIONS_PROMPT": "Conditions d'emploi des produits, doses, stades, délais, restrictions",
            "SAFETY_CLASSIFICATIONS_PROMPT": "Classifications de sécurité, pictogrammes, phrases de risque, équipements",
            "PRODUCT_SUBSTITUTION_PROMPT": "Alternatives aux produits, substitutions, équivalences, biocontrôle",
            "COMPLIANCE_CHECK_PROMPT": "Vérification de conformité, respect des réglementations, audits",
            "ENVIRONMENTAL_REGULATIONS_PROMPT": "Réglementation environnementale, ZNT, protection de l'environnement",
            
            # Weather Prompts
            "WEATHER_CHAT_PROMPT": "Conseil météorologique général, conditions d'intervention, fenêtres météo",
            "WEATHER_FORECAST_PROMPT": "Prévisions météorologiques, température, pluie, vent, humidité",
            "INTERVENTION_WINDOW_PROMPT": "Fenêtres d'intervention optimales, conditions météo favorables",
            "WEATHER_RISK_ANALYSIS_PROMPT": "Analyse des risques météorologiques, gel, grêle, tempêtes",
            "IRRIGATION_PLANNING_PROMPT": "Planification de l'irrigation, besoins en eau, ETR, bilan hydrique",
            "EVAPOTRANSPIRATION_PROMPT": "Calcul de l'évapotranspiration, coefficients culturaux, besoins hydriques",
            "CLIMATE_ADAPTATION_PROMPT": "Adaptation au changement climatique, variétés résistantes, pratiques",
            
            # Crop Health Prompts
            "CROP_HEALTH_CHAT_PROMPT": "Conseil phytosanitaire général, diagnostic, protection des cultures",
            "DISEASE_DIAGNOSIS_PROMPT": "Diagnostic des maladies, symptômes, identification, traitement",
            "PEST_IDENTIFICATION_PROMPT": "Identification des ravageurs, dégâts, seuils, lutte",
            "NUTRIENT_DEFICIENCY_PROMPT": "Analyse des carences nutritionnelles, symptômes, fertilisation",
            "TREATMENT_PLAN_PROMPT": "Plan de traitement, stratégie de protection, produits, calendrier",
            "RESISTANCE_MANAGEMENT_PROMPT": "Gestion de la résistance, alternance, rotation des modes d'action",
            "BIOLOGICAL_CONTROL_PROMPT": "Lutte biologique, auxiliaires, produits de biocontrôle",
            "THRESHOLD_MANAGEMENT_PROMPT": "Gestion des seuils d'intervention, comptage, surveillance",
            
            # Planning Prompts
            "PLANNING_CHAT_PROMPT": "Planification agricole générale, organisation des travaux, optimisation",
            "TASK_PLANNING_PROMPT": "Planification des tâches, séquencement, priorisation, calendrier",
            "RESOURCE_OPTIMIZATION_PROMPT": "Optimisation des ressources, matériel, main-d'œuvre, intrants",
            "SEASONAL_PLANNING_PROMPT": "Planification saisonnière, calendrier cultural, gestion des pics",
            "WEATHER_DEPENDENT_PLANNING_PROMPT": "Planification météo-dépendante, adaptation aux conditions",
            "COST_OPTIMIZATION_PROMPT": "Optimisation des coûts, minimisation des dépenses, efficience",
            "EMERGENCY_PLANNING_PROMPT": "Planification d'urgence, réorganisation, gestion des aléas",
            "WORKFLOW_OPTIMIZATION_PROMPT": "Optimisation des workflows, amélioration des processus",
            
            # Sustainability Prompts
            "SUSTAINABILITY_CHAT_PROMPT": "Conseil en durabilité général, performance environnementale, certifications",
            "CARBON_FOOTPRINT_PROMPT": "Calcul de l'empreinte carbone, émissions, stockage, bilan",
            "BIODIVERSITY_ASSESSMENT_PROMPT": "Évaluation de la biodiversité, auxiliaires, habitats, diversité",
            "SOIL_HEALTH_PROMPT": "Analyse de la santé des sols, matière organique, structure, vie biologique",
            "WATER_MANAGEMENT_PROMPT": "Gestion de l'eau, consommation, efficience, protection des ressources",
            "ENERGY_EFFICIENCY_PROMPT": "Efficacité énergétique, consommation, énergies renouvelables",
            "CERTIFICATION_SUPPORT_PROMPT": "Support à la certification, bio, HVE, préparation aux audits",
            "CIRCULAR_ECONOMY_PROMPT": "Économie circulaire, valorisation des déchets, autonomie",
            "CLIMATE_ADAPTATION_PROMPT": "Adaptation climatique, résilience, variétés, pratiques"
        }
        
        if self.embedding_model:
            self._compute_prompt_embeddings(prompt_descriptions)
        else:
            logger.warning("No embedding model available, using fallback matching")
    
    def _compute_prompt_embeddings(self, prompt_descriptions: Dict[str, str]):
        """Compute embeddings for all prompts."""
        try:
            descriptions = list(prompt_descriptions.values())
            prompt_names = list(prompt_descriptions.keys())
            
            # Compute sentence transformer embeddings
            embeddings = self.embedding_model.encode(descriptions)
            
            # Compute TF-IDF embeddings as backup
            self.tfidf_embeddings = self.tfidf_vectorizer.fit_transform(descriptions)
            self.prompt_descriptions = descriptions
            
            # Store embeddings
            for i, prompt_name in enumerate(prompt_names):
                agent_type = self._get_agent_type(prompt_name)
                prompt_type = self._get_prompt_type(prompt_name)
                
                self.prompt_embeddings[prompt_name] = PromptEmbedding(
                    prompt_name=prompt_name,
                    agent_type=agent_type,
                    prompt_type=prompt_type,
                    embedding=embeddings[i],
                    metadata={
                        "description": prompt_descriptions[prompt_name],
                        "model": self.model_name
                    },
                    created_at=datetime.now()
                )
            
            logger.info(f"Computed embeddings for {len(self.prompt_embeddings)} prompts")
            
        except Exception as e:
            logger.error(f"Error computing prompt embeddings: {e}")
            self.prompt_embeddings = {}
    
    def _get_agent_type(self, prompt_name: str) -> str:
        """Get agent type from prompt name."""
        if "FARM_DATA" in prompt_name:
            return "farm_data_agent"
        elif "REGULATORY" in prompt_name:
            return "regulatory_agent"
        elif "WEATHER" in prompt_name:
            return "weather_agent"
        elif "CROP_HEALTH" in prompt_name:
            return "crop_health_agent"
        elif "PLANNING" in prompt_name:
            return "planning_agent"
        elif "SUSTAINABILITY" in prompt_name:
            return "sustainability_agent"
        else:
            return "orchestrator"
    
    def _get_prompt_type(self, prompt_name: str) -> str:
        """Get prompt type from prompt name."""
        if "CHAT" in prompt_name:
            return "chat"
        elif "ANALYSIS" in prompt_name:
            return "analysis"
        elif "PLANNING" in prompt_name:
            return "planning"
        elif "DIAGNOSIS" in prompt_name:
            return "diagnosis"
        elif "OPTIMIZATION" in prompt_name:
            return "optimization"
        else:
            return "specialized"
    
    def find_best_prompt(self, query: str, context: str = "", 
                        agent_type: str = None, top_k: int = 5) -> List[PromptMatch]:
        """
        Find the best matching prompts for a query.
        
        Args:
            query: User query
            context: Additional context
            agent_type: Filter by agent type (optional)
            top_k: Number of top matches to return
            
        Returns:
            List of best matching prompts
        """
        if not self.embedding_model or not self.prompt_embeddings:
            return self._fallback_matching(query, context, agent_type, top_k)
        
        try:
            # Encode the query
            query_text = f"{query} {context}"
            query_embedding = self.embedding_model.encode([query_text])[0]
            
            # Compute similarities
            similarities = []
            for prompt_name, prompt_embedding in self.prompt_embeddings.items():
                # Filter by agent type if specified
                if agent_type and prompt_embedding.agent_type != agent_type:
                    continue
                
                # Compute cosine similarity
                similarity = cosine_similarity([query_embedding], [prompt_embedding.embedding])[0][0]
                
                similarities.append(PromptMatch(
                    prompt_name=prompt_name,
                    similarity_score=float(similarity),
                    agent_type=prompt_embedding.agent_type,
                    prompt_type=prompt_embedding.prompt_type,
                    reasoning=f"Semantic similarity: {similarity:.3f}",
                    metadata=prompt_embedding.metadata
                ))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x.similarity_score, reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error in semantic matching: {e}")
            return self._fallback_matching(query, context, agent_type, top_k)
    
    def find_prompt_by_intent(self, intent: str, context: str = "") -> Optional[PromptMatch]:
        """
        Find prompt by specific intent.
        
        Args:
            intent: Intent identifier (e.g., "AMM_LOOKUP", "WEATHER_FORECAST")
            context: Additional context
            
        Returns:
            Best matching prompt or None
        """
        # Direct mapping for common intents
        intent_mapping = {
            "AMM_LOOKUP": "AMM_LOOKUP_PROMPT",
            "WEATHER_FORECAST": "WEATHER_FORECAST_PROMPT",
            "DISEASE_DIAGNOSIS": "DISEASE_DIAGNOSIS_PROMPT",
            "TASK_PLANNING": "TASK_PLANNING_PROMPT",
            "CARBON_FOOTPRINT": "CARBON_FOOTPRINT_PROMPT",
            "PERFORMANCE_METRICS": "PERFORMANCE_METRICS_PROMPT",
            "PARCEL_ANALYSIS": "PARCEL_ANALYSIS_PROMPT",
            "INTERVENTION_WINDOW": "INTERVENTION_WINDOW_PROMPT",
            "TREATMENT_PLAN": "TREATMENT_PLAN_PROMPT",
            "SOIL_HEALTH": "SOIL_HEALTH_PROMPT"
        }
        
        prompt_name = intent_mapping.get(intent)
        if prompt_name and prompt_name in self.prompt_embeddings:
            prompt_embedding = self.prompt_embeddings[prompt_name]
            return PromptMatch(
                prompt_name=prompt_name,
                similarity_score=1.0,
                agent_type=prompt_embedding.agent_type,
                prompt_type=prompt_embedding.prompt_type,
                reasoning=f"Direct intent mapping: {intent}",
                metadata=prompt_embedding.metadata
            )
        
        # Fallback to semantic search
        matches = self.find_best_prompt(intent, context, top_k=1)
        return matches[0] if matches else None
    
    def _fallback_matching(self, query: str, context: str = "", 
                          agent_type: str = None, top_k: int = 5) -> List[PromptMatch]:
        """Fallback matching when embeddings are not available."""
        # Simple keyword-based matching
        query_lower = query.lower()
        
        # Define keyword patterns
        patterns = {
            "AMM_LOOKUP_PROMPT": ["amm", "autorisation", "roundup", "glyphosate"],
            "WEATHER_FORECAST_PROMPT": ["météo", "prévision", "temps", "pluie"],
            "DISEASE_DIAGNOSIS_PROMPT": ["maladie", "tache", "symptôme", "diagnostic"],
            "TASK_PLANNING_PROMPT": ["planifier", "organiser", "travaux", "planning"],
            "CARBON_FOOTPRINT_PROMPT": ["carbone", "empreinte", "co2", "émission"],
            "PERFORMANCE_METRICS_PROMPT": ["rendement", "performance", "métrique", "analyse"]
        }
        
        matches = []
        for prompt_name, keywords in patterns.items():
            if agent_type and self._get_agent_type(prompt_name) != agent_type:
                continue
            
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                matches.append(PromptMatch(
                    prompt_name=prompt_name,
                    similarity_score=score / len(keywords),
                    agent_type=self._get_agent_type(prompt_name),
                    prompt_type=self._get_prompt_type(prompt_name),
                    reasoning=f"Keyword matching: {score} matches",
                    metadata={"method": "fallback_keywords"}
                ))
        
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_k]
    
    def get_prompt_embeddings(self) -> Dict[str, PromptEmbedding]:
        """Get all prompt embeddings."""
        return self.prompt_embeddings.copy()
    
    def add_prompt_embedding(self, prompt_name: str, description: str, 
                           agent_type: str, prompt_type: str) -> bool:
        """Add a new prompt embedding."""
        if not self.embedding_model:
            return False
        
        try:
            embedding = self.embedding_model.encode([description])[0]
            
            self.prompt_embeddings[prompt_name] = PromptEmbedding(
                prompt_name=prompt_name,
                agent_type=agent_type,
                prompt_type=prompt_type,
                embedding=embedding,
                metadata={
                    "description": description,
                    "model": self.model_name
                },
                created_at=datetime.now()
            )
            
            logger.info(f"Added embedding for prompt: {prompt_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding prompt embedding: {e}")
            return False
    
    def save_embeddings(self, filepath: str) -> bool:
        """Save embeddings to file."""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.prompt_embeddings, f)
            logger.info(f"Saved embeddings to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            return False
    
    def load_embeddings(self, filepath: str) -> bool:
        """Load embeddings from file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    self.prompt_embeddings = pickle.load(f)
                logger.info(f"Loaded embeddings from {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return False

# Global embedding matcher instance
embedding_matcher = EmbeddingPromptMatcher()

# Convenience functions
def find_best_prompt(query: str, context: str = "", agent_type: str = None) -> Optional[PromptMatch]:
    """Find the best matching prompt for a query."""
    matches = embedding_matcher.find_best_prompt(query, context, agent_type, top_k=1)
    return matches[0] if matches else None

def find_prompt_by_intent(intent: str, context: str = "") -> Optional[PromptMatch]:
    """Find prompt by specific intent."""
    return embedding_matcher.find_prompt_by_intent(intent, context)

def get_prompt_name_for_query(query: str, context: str = "") -> str:
    """Get the prompt name for a user query."""
    match = find_best_prompt(query, context)
    return match.prompt_name if match else "FARM_DATA_CHAT_PROMPT"

# Export all classes and functions
__all__ = [
    "EmbeddingPromptMatcher",
    "PromptEmbedding",
    "PromptMatch",
    "embedding_matcher",
    "find_best_prompt",
    "find_prompt_by_intent",
    "get_prompt_name_for_query"
]
