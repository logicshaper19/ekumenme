"""
Semantic Tool Selection Service
Provides intelligent tool selection using semantic similarity and intent classification.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from langchain.tools import BaseTool

# Optional imports for enhanced functionality
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SentenceTransformer = None
    np = None
    cosine_similarity = None

logger = logging.getLogger(__name__)

@dataclass
class ToolSelectionResult:
    """Result of tool selection process."""
    selected_tools: List[str]
    tool_scores: Dict[str, float]
    selection_method: str
    confidence: float
    reasoning: str
    alternative_tools: List[Tuple[str, float]]

@dataclass
class ToolProfile:
    """Profile of a tool with semantic information."""
    name: str
    description: str
    keywords: List[str]
    semantic_tags: List[str]
    use_cases: List[str]
    input_types: List[str]
    output_types: List[str]
    domain: str
    complexity: str
    embedding: Optional[Any] = None  # np.ndarray when available

class SemanticToolSelector:
    """
    Semantic tool selection service using multiple methods:
    1. Semantic similarity with sentence transformers
    2. Keyword-based matching with scoring
    3. Intent-based tool mapping
    4. Hybrid approach combining all methods
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize semantic tool selector."""
        if SEMANTIC_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(model_name)
                logger.info(f"Loaded sentence transformer model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}, using fallback")
                self.encoder = None
        else:
            logger.info("Sentence transformers not available, using keyword-based selection only")
            self.encoder = None
        
        self.tool_profiles: Dict[str, ToolProfile] = {}
        self.intent_tool_mapping: Dict[str, List[str]] = {}
        self._initialize_tool_profiles()
        self._initialize_intent_mapping()
    
    def _initialize_tool_profiles(self):
        """Initialize tool profiles with semantic information."""
        # Crop Health Tools
        self.tool_profiles["diagnose_disease_tool"] = ToolProfile(
            name="diagnose_disease_tool",
            description="Diagnostique les maladies des cultures à partir des symptômes observés",
            keywords=["maladie", "champignon", "bactérie", "virus", "symptôme", "diagnostic", "pathologie"],
            semantic_tags=["health", "disease", "diagnosis", "pathology", "symptoms", "crop_protection"],
            use_cases=[
                "identifier une maladie sur les cultures",
                "analyser des symptômes de maladie",
                "diagnostic phytosanitaire",
                "problèmes de santé des plantes"
            ],
            input_types=["crop_type", "symptoms", "environmental_conditions"],
            output_types=["disease_diagnosis", "treatment_recommendations"],
            domain="crop_health",
            complexity="medium"
        )
        
        self.tool_profiles["identify_pest_tool"] = ToolProfile(
            name="identify_pest_tool",
            description="Identifie les ravageurs des cultures à partir des dégâts observés",
            keywords=["ravageur", "insecte", "puceron", "chenille", "dégât", "pest", "nuisible"],
            semantic_tags=["pest", "insect", "damage", "identification", "crop_protection", "entomology"],
            use_cases=[
                "identifier des ravageurs sur les cultures",
                "analyser des dégâts d'insectes",
                "reconnaissance de nuisibles",
                "problèmes d'insectes"
            ],
            input_types=["crop_type", "damage_symptoms", "pest_indicators"],
            output_types=["pest_identification", "control_methods"],
            domain="crop_health",
            complexity="medium"
        )
        
        # Planning Tools
        self.tool_profiles["generate_planning_tasks_tool"] = ToolProfile(
            name="generate_planning_tasks_tool",
            description="Génère des tâches de planification pour les opérations agricoles",
            keywords=["planification", "tâche", "organisation", "calendrier", "travaux", "planning"],
            semantic_tags=["planning", "tasks", "scheduling", "operations", "workflow", "management"],
            use_cases=[
                "planifier les travaux agricoles",
                "organiser les tâches de la saison",
                "créer un calendrier cultural",
                "optimiser les opérations"
            ],
            input_types=["crops", "surface", "planning_objective"],
            output_types=["planning_tasks", "task_schedule"],
            domain="planning",
            complexity="high"
        )
        
        # Regulatory Tools
        self.tool_profiles["check_regulatory_compliance_tool"] = ToolProfile(
            name="check_regulatory_compliance_tool",
            description="Vérifie la conformité réglementaire des pratiques agricoles",
            keywords=["conformité", "réglementation", "légal", "autorisation", "compliance", "règles"],
            semantic_tags=["compliance", "regulation", "legal", "authorization", "safety", "rules"],
            use_cases=[
                "vérifier la conformité réglementaire",
                "contrôler les autorisations",
                "respecter la législation",
                "validation légale"
            ],
            input_types=["practice_type", "products_used", "location", "timing"],
            output_types=["compliance_status", "violations", "recommendations"],
            domain="regulatory",
            complexity="high"
        )
        
        self.tool_profiles["database_integrated_amm_lookup_tool"] = ToolProfile(
            name="database_integrated_amm_lookup_tool",
            description="Recherche d'autorisations AMM dans la base de données EPHY",
            keywords=["amm", "autorisation", "produit", "phytosanitaire", "ephy", "homologation"],
            semantic_tags=["amm", "authorization", "product", "phytosanitary", "ephy", "approval"],
            use_cases=[
                "vérifier l'autorisation d'un produit",
                "rechercher un numéro AMM",
                "contrôler l'homologation",
                "validation produit phytosanitaire"
            ],
            input_types=["product_name", "active_ingredient", "crop_type"],
            output_types=["amm_status", "product_details", "usage_conditions"],
            domain="regulatory",
            complexity="medium"
        )
        
        # Weather Tools
        self.tool_profiles["get_weather_data_tool"] = ToolProfile(
            name="get_weather_data_tool",
            description="Récupère les données météorologiques pour l'agriculture",
            keywords=["météo", "temps", "prévision", "climat", "température", "pluie", "vent"],
            semantic_tags=["weather", "forecast", "climate", "temperature", "precipitation", "conditions"],
            use_cases=[
                "obtenir les prévisions météo",
                "analyser les conditions climatiques",
                "planifier selon la météo",
                "risques météorologiques"
            ],
            input_types=["location", "date_range", "weather_type"],
            output_types=["weather_forecast", "climate_data", "weather_alerts"],
            domain="weather",
            complexity="low"
        )
        
        # Farm Data Tools
        self.tool_profiles["get_farm_data_tool"] = ToolProfile(
            name="get_farm_data_tool",
            description="Récupère les données de l'exploitation agricole",
            keywords=["exploitation", "parcelle", "données", "ferme", "terrain", "surface"],
            semantic_tags=["farm", "field", "data", "parcel", "land", "agricultural_data"],
            use_cases=[
                "obtenir les données de l'exploitation",
                "analyser les parcelles",
                "informations terrain",
                "données agricoles"
            ],
            input_types=["farm_id", "parcel_id", "data_type"],
            output_types=["farm_data", "parcel_info", "agricultural_metrics"],
            domain="farm_data",
            complexity="low"
        )
        
        # Generate embeddings for all tool profiles
        self._generate_tool_embeddings()
    
    def _generate_tool_embeddings(self):
        """Generate embeddings for all tool profiles."""
        if not self.encoder or not SEMANTIC_AVAILABLE:
            return
        
        for tool_name, profile in self.tool_profiles.items():
            # Combine description, keywords, and use cases for embedding
            text_for_embedding = f"{profile.description} {' '.join(profile.keywords)} {' '.join(profile.use_cases)} {' '.join(profile.semantic_tags)}"
            
            try:
                embedding = self.encoder.encode(text_for_embedding)
                profile.embedding = embedding
                logger.debug(f"Generated embedding for tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to generate embedding for {tool_name}: {e}")
    
    def _initialize_intent_mapping(self):
        """Initialize intent to tool mapping."""
        self.intent_tool_mapping = {
            "disease_diagnosis": ["diagnose_disease_tool"],
            "pest_identification": ["identify_pest_tool"],
            "planning": ["generate_planning_tasks_tool"],
            "compliance_check": ["check_regulatory_compliance_tool"],
            "amm_lookup": ["database_integrated_amm_lookup_tool"],
            "weather_forecast": ["get_weather_data_tool"],
            "farm_data_analysis": ["get_farm_data_tool"],
            "crop_health": ["diagnose_disease_tool", "identify_pest_tool"],
            "regulatory": ["check_regulatory_compliance_tool", "database_integrated_amm_lookup_tool"]
        }
    
    def select_tools(
        self, 
        message: str, 
        available_tools: List[str],
        method: str = "hybrid",
        threshold: float = 0.6,
        max_tools: int = 3
    ) -> ToolSelectionResult:
        """
        Select tools using specified method.
        
        Args:
            message: User message or query
            available_tools: List of available tool names
            method: Selection method ("semantic", "keyword", "intent", "hybrid")
            threshold: Minimum score threshold for tool selection
            max_tools: Maximum number of tools to select
        
        Returns:
            ToolSelectionResult with selected tools and metadata
        """
        try:
            if method == "semantic":
                return self._select_tools_semantic(message, available_tools, threshold, max_tools)
            elif method == "keyword":
                return self._select_tools_keyword(message, available_tools, threshold, max_tools)
            elif method == "intent":
                return self._select_tools_intent(message, available_tools, threshold, max_tools)
            elif method == "hybrid":
                return self._select_tools_hybrid(message, available_tools, threshold, max_tools)
            else:
                return self._select_tools_fallback(message, available_tools, threshold, max_tools)
        
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            return self._select_tools_fallback(message, available_tools, threshold, max_tools)
    
    def _select_tools_semantic(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int
    ) -> ToolSelectionResult:
        """Select tools using semantic similarity."""
        if not self.encoder or not SEMANTIC_AVAILABLE:
            return self._select_tools_fallback(message, available_tools, threshold, max_tools)
        
        # Generate message embedding
        message_embedding = self.encoder.encode(message)
        
        # Calculate similarities
        tool_scores = {}
        for tool_name in available_tools:
            if tool_name in self.tool_profiles:
                profile = self.tool_profiles[tool_name]
                if profile.embedding is not None:
                    similarity = cosine_similarity(
                        message_embedding.reshape(1, -1),
                        profile.embedding.reshape(1, -1)
                    )[0][0]
                    tool_scores[tool_name] = float(similarity)
        
        # Select tools above threshold
        selected_tools = [
            tool for tool, score in tool_scores.items() 
            if score >= threshold
        ]
        
        # Sort by score and limit
        selected_tools = sorted(selected_tools, key=lambda t: tool_scores[t], reverse=True)[:max_tools]
        
        # Calculate confidence
        if SEMANTIC_AVAILABLE and selected_tools:
            confidence = np.mean([tool_scores[tool] for tool in selected_tools])
        else:
            confidence = sum(tool_scores[tool] for tool in selected_tools) / len(selected_tools) if selected_tools else 0.0
        
        # Get alternatives
        alternatives = [
            (tool, score) for tool, score in sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
            if tool not in selected_tools
        ][:3]
        
        return ToolSelectionResult(
            selected_tools=selected_tools,
            tool_scores=tool_scores,
            selection_method="semantic",
            confidence=confidence,
            reasoning=f"Semantic similarity analysis with {len(selected_tools)} tools above threshold {threshold}",
            alternative_tools=alternatives
        )

    def _select_tools_keyword(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int
    ) -> ToolSelectionResult:
        """Select tools using keyword matching with scoring."""
        message_lower = message.lower()
        tool_scores = {}

        for tool_name in available_tools:
            if tool_name in self.tool_profiles:
                profile = self.tool_profiles[tool_name]
                score = 0

                # Score based on keyword matches
                for keyword in profile.keywords:
                    if keyword.lower() in message_lower:
                        score += 1

                # Score based on semantic tags
                for tag in profile.semantic_tags:
                    if tag.lower() in message_lower:
                        score += 0.5

                # Score based on use case similarity
                for use_case in profile.use_cases:
                    use_case_words = use_case.lower().split()
                    matches = sum(1 for word in use_case_words if word in message_lower)
                    if matches > 0:
                        score += matches * 0.3

                # Normalize score
                max_possible_score = len(profile.keywords) + len(profile.semantic_tags) * 0.5 + len(profile.use_cases) * 3 * 0.3
                normalized_score = score / max_possible_score if max_possible_score > 0 else 0
                tool_scores[tool_name] = normalized_score

        # Select tools above threshold
        selected_tools = [
            tool for tool, score in tool_scores.items()
            if score >= threshold
        ]

        # Sort by score and limit
        selected_tools = sorted(selected_tools, key=lambda t: tool_scores[t], reverse=True)[:max_tools]

        # Calculate confidence
        confidence = sum(tool_scores[tool] for tool in selected_tools) / len(selected_tools) if selected_tools else 0.0

        # Get alternatives
        alternatives = [
            (tool, score) for tool, score in sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
            if tool not in selected_tools
        ][:3]

        return ToolSelectionResult(
            selected_tools=selected_tools,
            tool_scores=tool_scores,
            selection_method="keyword",
            confidence=confidence,
            reasoning=f"Keyword-based matching with {len(selected_tools)} tools above threshold {threshold}",
            alternative_tools=alternatives
        )

    def _select_tools_intent(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int
    ) -> ToolSelectionResult:
        """Select tools using intent classification."""
        # Simple intent classification based on message content
        message_lower = message.lower()
        detected_intents = []

        # Intent detection patterns
        intent_patterns = {
            "disease_diagnosis": ["maladie", "champignon", "bactérie", "virus", "symptôme", "diagnostic"],
            "pest_identification": ["ravageur", "insecte", "puceron", "chenille", "dégât", "nuisible"],
            "planning": ["planification", "tâche", "organisation", "calendrier", "travaux", "planning"],
            "compliance_check": ["conformité", "réglementation", "légal", "autorisation", "compliance"],
            "amm_lookup": ["amm", "autorisation", "produit", "phytosanitaire", "ephy"],
            "weather_forecast": ["météo", "temps", "prévision", "climat", "température"],
            "farm_data_analysis": ["exploitation", "parcelle", "données", "ferme", "terrain"]
        }

        # Detect intents
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                intent_scores[intent] = score / len(patterns)
                detected_intents.append(intent)

        # Map intents to tools
        tool_scores = {}
        for intent in detected_intents:
            if intent in self.intent_tool_mapping:
                intent_score = intent_scores[intent]
                for tool_name in self.intent_tool_mapping[intent]:
                    if tool_name in available_tools:
                        tool_scores[tool_name] = max(tool_scores.get(tool_name, 0), intent_score)

        # Select tools above threshold
        selected_tools = [
            tool for tool, score in tool_scores.items()
            if score >= threshold
        ]

        # Sort by score and limit
        selected_tools = sorted(selected_tools, key=lambda t: tool_scores[t], reverse=True)[:max_tools]

        # Calculate confidence
        confidence = sum(tool_scores[tool] for tool in selected_tools) / len(selected_tools) if selected_tools else 0.0

        # Get alternatives
        alternatives = [
            (tool, score) for tool, score in sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
            if tool not in selected_tools
        ][:3]

        return ToolSelectionResult(
            selected_tools=selected_tools,
            tool_scores=tool_scores,
            selection_method="intent",
            confidence=confidence,
            reasoning=f"Intent-based selection with detected intents: {detected_intents}",
            alternative_tools=alternatives
        )

    def _select_tools_hybrid(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int
    ) -> ToolSelectionResult:
        """Select tools using hybrid approach combining all methods."""
        # Get results from all methods
        semantic_result = self._select_tools_semantic(message, available_tools, threshold * 0.8, max_tools * 2)
        keyword_result = self._select_tools_keyword(message, available_tools, threshold * 0.8, max_tools * 2)
        intent_result = self._select_tools_intent(message, available_tools, threshold * 0.8, max_tools * 2)

        # Combine scores with weights
        weights = {
            "semantic": 0.4,
            "keyword": 0.35,
            "intent": 0.25
        }

        combined_scores = {}
        all_tools = set(semantic_result.tool_scores.keys()) | set(keyword_result.tool_scores.keys()) | set(intent_result.tool_scores.keys())

        for tool in all_tools:
            if tool in available_tools:
                score = 0
                score += semantic_result.tool_scores.get(tool, 0) * weights["semantic"]
                score += keyword_result.tool_scores.get(tool, 0) * weights["keyword"]
                score += intent_result.tool_scores.get(tool, 0) * weights["intent"]
                combined_scores[tool] = score

        # Select tools above threshold
        selected_tools = [
            tool for tool, score in combined_scores.items()
            if score >= threshold
        ]

        # Sort by score and limit
        selected_tools = sorted(selected_tools, key=lambda t: combined_scores[t], reverse=True)[:max_tools]

        # Calculate confidence
        confidence = sum(combined_scores[tool] for tool in selected_tools) / len(selected_tools) if selected_tools else 0.0

        # Get alternatives
        alternatives = [
            (tool, score) for tool, score in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            if tool not in selected_tools
        ][:3]

        # Generate detailed reasoning
        reasoning_parts = []
        if semantic_result.selected_tools:
            reasoning_parts.append(f"Semantic: {semantic_result.selected_tools}")
        if keyword_result.selected_tools:
            reasoning_parts.append(f"Keyword: {keyword_result.selected_tools}")
        if intent_result.selected_tools:
            reasoning_parts.append(f"Intent: {intent_result.selected_tools}")

        reasoning = f"Hybrid selection combining {', '.join(reasoning_parts)}"

        return ToolSelectionResult(
            selected_tools=selected_tools,
            tool_scores=combined_scores,
            selection_method="hybrid",
            confidence=confidence,
            reasoning=reasoning,
            alternative_tools=alternatives
        )

    def _select_tools_fallback(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int
    ) -> ToolSelectionResult:
        """Fallback tool selection using simple keyword matching."""
        message_lower = message.lower()
        tool_scores = {}

        # Simple keyword patterns for fallback
        fallback_patterns = {
            "diagnose_disease_tool": ["maladie", "disease", "symptôme", "champignon"],
            "identify_pest_tool": ["ravageur", "pest", "insecte", "dégât"],
            "generate_planning_tasks_tool": ["planning", "planification", "tâche", "calendrier"],
            "check_regulatory_compliance_tool": ["conformité", "réglementation", "compliance"],
            "database_integrated_amm_lookup_tool": ["amm", "autorisation", "produit"],
            "get_weather_data_tool": ["météo", "weather", "temps", "prévision"],
            "get_farm_data_tool": ["exploitation", "farm", "parcelle", "données"]
        }

        for tool_name in available_tools:
            if tool_name in fallback_patterns:
                patterns = fallback_patterns[tool_name]
                matches = sum(1 for pattern in patterns if pattern in message_lower)
                tool_scores[tool_name] = matches / len(patterns) if patterns else 0

        # Select tools above threshold
        selected_tools = [
            tool for tool, score in tool_scores.items()
            if score >= threshold
        ]

        # Sort by score and limit
        selected_tools = sorted(selected_tools, key=lambda t: tool_scores[t], reverse=True)[:max_tools]

        # If no tools selected, select the first available tool as fallback
        if not selected_tools and available_tools:
            selected_tools = [available_tools[0]]
            tool_scores[available_tools[0]] = 0.5

        # Calculate confidence
        confidence = sum(tool_scores[tool] for tool in selected_tools) / len(selected_tools) if selected_tools else 0.0

        return ToolSelectionResult(
            selected_tools=selected_tools,
            tool_scores=tool_scores,
            selection_method="fallback",
            confidence=confidence,
            reasoning="Fallback keyword matching due to semantic selection failure",
            alternative_tools=[]
        )

    def add_tool_profile(self, tool: BaseTool, domain: str = "general", complexity: str = "medium"):
        """Add a new tool profile dynamically."""
        profile = ToolProfile(
            name=tool.name,
            description=tool.description,
            keywords=self._extract_keywords_from_description(tool.description),
            semantic_tags=[],
            use_cases=[tool.description],
            input_types=[],
            output_types=[],
            domain=domain,
            complexity=complexity
        )

        # Generate embedding if encoder is available
        if self.encoder and SEMANTIC_AVAILABLE:
            text_for_embedding = f"{profile.description} {' '.join(profile.keywords)}"
            try:
                profile.embedding = self.encoder.encode(text_for_embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding for {tool.name}: {e}")

        self.tool_profiles[tool.name] = profile
        logger.info(f"Added tool profile for: {tool.name}")

    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """Extract keywords from tool description."""
        # Simple keyword extraction - could be enhanced with NLP
        words = description.lower().split()
        # Filter out common words
        stop_words = {"le", "la", "les", "de", "du", "des", "et", "ou", "pour", "avec", "dans", "sur", "par"}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:10]  # Limit to 10 keywords

    def get_tool_profile(self, tool_name: str) -> Optional[ToolProfile]:
        """Get tool profile by name."""
        return self.tool_profiles.get(tool_name)

    def list_available_tools(self, domain: Optional[str] = None) -> List[str]:
        """List available tools, optionally filtered by domain."""
        if domain:
            return [name for name, profile in self.tool_profiles.items() if profile.domain == domain]
        return list(self.tool_profiles.keys())


# Global semantic tool selector instance
semantic_tool_selector = SemanticToolSelector()

# Convenience functions
def select_tools_for_message(
    message: str,
    available_tools: List[str],
    method: str = "hybrid",
    threshold: float = 0.6,
    max_tools: int = 3
) -> ToolSelectionResult:
    """Select tools for a message using semantic tool selector."""
    return semantic_tool_selector.select_tools(message, available_tools, method, threshold, max_tools)

def add_tool_profile(tool: BaseTool, domain: str = "general", complexity: str = "medium"):
    """Add a tool profile to the global selector."""
    semantic_tool_selector.add_tool_profile(tool, domain, complexity)
