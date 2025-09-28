"""
Farm Data Manager Agent fully integrated with cost optimization, semantic search, and reasoning.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
import logging
import json
from datetime import datetime, timedelta

# Import from integrated system
try:
    from .base_agent import IntegratedAgriculturalAgent, AgentType, TaskComplexity
    # Remove circular import - use fallback SemanticKnowledgeRetriever
    from .base_agent import SemanticKnowledgeRetriever
except ImportError:
    # Fallback imports
    class AgentType:
        FARM_DATA = "farm_data"
    
    class TaskComplexity:
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"
        CRITICAL = "critical"
    
    class SemanticKnowledgeRetriever:
        def retrieve_relevant_knowledge(self, query: str, top_k: int = 3) -> List[str]:
            return ["Connaissance agricole générale disponible"]
    
    # Fallback base class
    class IntegratedAgriculturalAgent:
        def __init__(self, agent_type, description, llm_manager, knowledge_retriever, 
                     complexity_default=None, specialized_tools=None):
            self.agent_type = agent_type
            self.description = description
            self.llm_manager = llm_manager
            self.knowledge_retriever = knowledge_retriever
            self.complexity_default = complexity_default
            self.specialized_tools = specialized_tools or []
        
        def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
            return {"response": "Mock response", "agent_type": self.agent_type.value}
        
        def _get_agent_prompt_template(self) -> str:
            return "Mock prompt template"
        
        def _analyze_message_complexity(self, message: str, context: Dict[str, Any]):
            return TaskComplexity.MODERATE
        
        def _retrieve_domain_knowledge(self, message: str) -> List[str]:
            return ["Mock knowledge"]

logger = logging.getLogger(__name__)

class SemanticFarmDataTool(BaseTool):
    """Enhanced farm data tool with semantic understanding and cost optimization."""
    
    name: str = "semantic_farm_data_query"
    description: str = "Interroger les données agricoles avec compréhension sémantique"
    
    def __init__(self, database_manager=None, knowledge_retriever: SemanticKnowledgeRetriever = None, **kwargs):
        super().__init__(**kwargs)
        self._db = database_manager or EnhancedMockDatabaseManager()
        self.knowledge_retriever = knowledge_retriever
    
    def _run(self, natural_query: str, context: Dict[str, Any] = None) -> str:
        """Execute semantic farm data query with intelligent interpretation."""
        
        try:
            # Parse natural language query semantically
            query_analysis = self._analyze_query_semantically(natural_query)
            
            # Retrieve relevant agricultural knowledge
            agricultural_context = []
            if self.knowledge_retriever:
                agricultural_context = self.knowledge_retriever.retrieve_relevant_knowledge(
                    f"données exploitation {natural_query}", top_k=3
                )
            
            # Execute database query based on semantic analysis
            data = self._execute_semantic_query(query_analysis, context)
            
            # Enhance results with semantic insights
            enhanced_results = self._enhance_results_with_context(
                data, query_analysis, agricultural_context
            )
            
            return json.dumps(enhanced_results, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Semantic farm data query error: {e}")
            return json.dumps({"error": "Erreur lors de l'analyse sémantique des données"})
    
    def _analyze_query_semantically(self, query: str) -> Dict[str, Any]:
        """Analyze query using semantic understanding."""
        query_lower = query.lower()
        
        analysis = {
            "intent": self._detect_query_intent(query_lower),
            "entities": self._extract_entities(query_lower),
            "temporal_scope": self._extract_temporal_scope(query_lower),
            "comparison_type": self._detect_comparison_type(query_lower),
            "aggregation_level": self._detect_aggregation_level(query_lower)
        }
        
        return analysis
    
    def _detect_query_intent(self, query: str) -> str:
        """Detect the main intent of the query."""
        intent_patterns = {
            "performance_analysis": ["performance", "analyse", "évolution", "tendance"],
            "comparison": ["compare", "différence", "versus", "par rapport"],
            "optimization": ["optimise", "améliore", "meilleur", "efficace"],
            "reporting": ["rapport", "bilan", "résumé", "synthèse"],
            "monitoring": ["surveille", "suivi", "état", "situation"],
            "forecasting": ["prévision", "projection", "estimation", "prédiction"]
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in query for pattern in patterns):
                return intent
        
        return "data_retrieval"  # Default
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract agricultural entities from query."""
        entities = {
            "crops": [],
            "parcels": [],
            "operations": [],
            "metrics": [],
            "time_periods": []
        }
        
        # Crop detection
        crop_keywords = {
            "blé": ["blé", "wheat"], "orge": ["orge", "barley"], 
            "maïs": ["maïs", "corn"], "colza": ["colza", "canola"],
            "tournesol": ["tournesol", "sunflower"]
        }
        
        for crop, keywords in crop_keywords.items():
            if any(keyword in query for keyword in keywords):
                entities["crops"].append(crop)
        
        # Metric detection
        metric_keywords = {
            "rendement": ["rendement", "yield", "production"],
            "coût": ["coût", "prix", "budget", "dépense"],
            "marge": ["marge", "bénéfice", "rentabilité"],
            "surface": ["surface", "hectare", "ha"]
        }
        
        for metric, keywords in metric_keywords.items():
            if any(keyword in query for keyword in keywords):
                entities["metrics"].append(metric)
        
        return entities
    
    def _extract_temporal_scope(self, query: str) -> Dict[str, Any]:
        """Extract temporal information from query."""
        temporal_patterns = {
            "current_year": ["cette année", "2024", "actuel"],
            "last_year": ["année dernière", "2023", "précédent"],
            "multi_year": ["années", "historique", "évolution"],
            "season": ["campagne", "saison", "récolte"],
            "monthly": ["mois", "mensuel", "trimestre"]
        }
        
        scope = {"type": "current_year", "specific_years": [], "range": None}
        
        for pattern_type, patterns in temporal_patterns.items():
            if any(pattern in query for pattern in patterns):
                scope["type"] = pattern_type
                break
        
        # Extract specific years
        import re
        years = re.findall(r'\b(20\d{2})\b', query)
        scope["specific_years"] = years
        
        return scope
    
    def _detect_comparison_type(self, query: str) -> str:
        """Detect type of comparison requested."""
        if any(word in query for word in ["versus", "vs", "par rapport", "compare"]):
            return "comparative"
        elif any(word in query for word in ["évolution", "tendance", "progression"]):
            return "temporal"
        elif any(word in query for word in ["moyenne", "médiane", "percentile"]):
            return "statistical"
        else:
            return "none"
    
    def _detect_aggregation_level(self, query: str) -> str:
        """Detect desired aggregation level."""
        if any(word in query for word in ["parcelle", "champ", "détail"]):
            return "parcel"
        elif any(word in query for word in ["exploitation", "ferme", "total"]):
            return "farm"
        elif any(word in query for word in ["région", "département", "secteur"]):
            return "regional"
        else:
            return "farm"  # Default
    
    def _execute_semantic_query(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database query based on semantic analysis."""
        intent = analysis["intent"]
        entities = analysis["entities"]
        temporal = analysis["temporal_scope"]
        
        # Build query parameters
        filters = self._build_filters_from_entities(entities, context)
        date_range = self._build_date_range_from_temporal(temporal)
        
        # Execute appropriate query based on intent
        if intent == "performance_analysis":
            return self._get_performance_data(filters, date_range, analysis)
        elif intent == "comparison":
            return self._get_comparison_data(filters, date_range, analysis)
        elif intent == "optimization":
            return self._get_optimization_data(filters, date_range, analysis)
        else:
            return self._get_general_data(filters, date_range, analysis)
    
    def _build_filters_from_entities(self, entities: Dict[str, List[str]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Build database filters from extracted entities."""
        filters = {}
        
        if context and 'farm_id' in context:
            filters['farm_id'] = context['farm_id']
        
        if entities["crops"]:
            filters['crop_type'] = entities["crops"]
        
        return filters
    
    def _build_date_range_from_temporal(self, temporal: Dict[str, Any]) -> Optional[tuple]:
        """Build date range from temporal analysis."""
        if temporal["type"] == "current_year":
            return ("2024-01-01", "2024-12-31")
        elif temporal["type"] == "last_year":
            return ("2023-01-01", "2023-12-31")
        elif temporal["type"] == "multi_year":
            return ("2020-01-01", "2024-12-31")
        elif temporal["specific_years"]:
            year = temporal["specific_years"][0]
            return (f"{year}-01-01", f"{year}-12-31")
        
        return None
    
    def _get_performance_data(self, filters: Dict[str, Any], date_range: Optional[tuple], 
                            analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance analysis data."""
        data = self._db.get_performance_analysis(filters, date_range)
        
        return {
            "query_type": "performance_analysis",
            "data": data,
            "insights": self._generate_performance_insights(data),
            "semantic_analysis": analysis
        }
    
    def _get_comparison_data(self, filters: Dict[str, Any], date_range: Optional[tuple],
                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get comparison data."""
        data = self._db.get_comparison_data(filters, date_range)
        
        return {
            "query_type": "comparison",
            "data": data,
            "insights": self._generate_comparison_insights(data),
            "semantic_analysis": analysis
        }
    
    def _get_optimization_data(self, filters: Dict[str, Any], date_range: Optional[tuple],
                             analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimization recommendations."""
        data = self._db.get_optimization_opportunities(filters, date_range)
        
        return {
            "query_type": "optimization",
            "data": data,
            "recommendations": self._generate_optimization_recommendations(data),
            "semantic_analysis": analysis
        }
    
    def _get_general_data(self, filters: Dict[str, Any], date_range: Optional[tuple],
                        analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get general farm data."""
        data = self._db.get_general_farm_data(filters, date_range)
        
        return {
            "query_type": "general",
            "data": data,
            "summary": self._generate_summary_stats(data),
            "semantic_analysis": analysis
        }
    
    def _enhance_results_with_context(self, data: Dict[str, Any], 
                                    analysis: Dict[str, Any],
                                    agricultural_context: List[str]) -> Dict[str, Any]:
        """Enhance results with agricultural context and insights."""
        enhanced = data.copy()
        
        enhanced["agricultural_context"] = agricultural_context
        enhanced["contextual_insights"] = self._generate_contextual_insights(
            data, agricultural_context
        )
        enhanced["action_recommendations"] = self._generate_action_recommendations(
            data, analysis
        )
        
        return enhanced
    
    def _generate_performance_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from performance data."""
        return [
            "Analyse des performances en cours...",
            "Tendances identifiées dans les données",
            "Comparaison avec les objectifs de l'exploitation"
        ]
    
    def _generate_comparison_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate comparison insights."""
        return [
            "Analyse comparative des parcelles",
            "Identification des meilleures performances",
            "Facteurs de différenciation identifiés"
        ]
    
    def _generate_optimization_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations."""
        return [
            "Optimisation des intrants recommandée",
            "Ajustement des pratiques culturales",
            "Amélioration de la rentabilité possible"
        ]
    
    def _generate_summary_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_records": len(data.get("records", [])),
            "data_quality": "good",
            "completeness": 0.95
        }
    
    def _generate_contextual_insights(self, data: Dict[str, Any], 
                                    context: List[str]) -> List[str]:
        """Generate insights using agricultural context."""
        insights = []
        
        if context:
            insights.append("Données analysées dans le contexte agricole français")
            insights.append("Référentiels techniques appliqués")
        
        return insights
    
    def _generate_action_recommendations(self, data: Dict[str, Any],
                                       analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        intent = analysis.get("intent", "")
        
        if intent == "optimization":
            return [
                "Réviser les pratiques sur les parcelles moins performantes",
                "Analyser les coûts de production en détail",
                "Considérer l'ajustement des variétés cultivées"
            ]
        elif intent == "performance_analysis":
            return [
                "Surveiller les indicateurs de performance clés",
                "Identifier les facteurs de succès reproductibles",
                "Planifier les améliorations pour la prochaine campagne"
            ]
        
        return ["Continuer le suivi des données de l'exploitation"]

class EnhancedMockDatabaseManager:
    """Enhanced mock database with performance analysis capabilities."""
    
    def get_performance_analysis(self, filters: Dict[str, Any], date_range: Optional[tuple]) -> Dict[str, Any]:
        """Mock performance analysis data."""
        return {
            "records": [
                {
                    "parcelle": "Grande Pièce",
                    "culture": "blé",
                    "rendement_2024": 75.2,
                    "rendement_2023": 68.5,
                    "evolution": "+9.8%",
                    "performance_relative": "excellente"
                }
            ],
            "kpi": {
                "rendement_moyen": 71.8,
                "progression_annuelle": 6.2,
                "rang_performance": "top 25%"
            }
        }
    
    def get_comparison_data(self, filters: Dict[str, Any], date_range: Optional[tuple]) -> Dict[str, Any]:
        """Mock comparison data."""
        return {
            "comparisons": [
                {
                    "parcelle_a": "Grande Pièce",
                    "parcelle_b": "Champ du Bas", 
                    "difference_rendement": "+12.3 q/ha",
                    "difference_cout": "-45€/ha",
                    "avantage": "Grande Pièce"
                }
            ]
        }
    
    def get_optimization_opportunities(self, filters: Dict[str, Any], date_range: Optional[tuple]) -> Dict[str, Any]:
        """Mock optimization opportunities."""
        return {
            "opportunities": [
                {
                    "type": "reduction_intrants",
                    "description": "Optimisation de la fertilisation azotée",
                    "gain_potentiel": "180€/ha",
                    "niveau_difficulte": "modéré"
                }
            ]
        }
    
    def get_general_farm_data(self, filters: Dict[str, Any], date_range: Optional[tuple]) -> Dict[str, Any]:
        """Mock general farm data."""
        return {
            "records": [
                {
                    "parcelle": "Grande Pièce",
                    "surface": 12.5,
                    "culture": "blé",
                    "rendement": 75.2
                }
            ]
        }

class IntegratedFarmDataAgent(IntegratedAgriculturalAgent):
    """Farm Data Manager Agent fully integrated with the system architecture."""
    
    def __init__(self, llm_manager, knowledge_retriever: SemanticKnowledgeRetriever, 
                 database_config=None):
        
        # Initialize enhanced tools
        tools = [
            SemanticFarmDataTool(database_config, knowledge_retriever)
        ]
        
        super().__init__(
            agent_type=AgentType.FARM_DATA,
            description="Expert en analyse de données d'exploitation agricole française",
            llm_manager=llm_manager,
            knowledge_retriever=knowledge_retriever,
            complexity_default=TaskComplexity.MODERATE,
            specialized_tools=tools
        )
        
        self.database_config = database_config
        logger.info("Initialized Integrated Farm Data Manager Agent")
    
    def _get_agent_prompt_template(self) -> str:
        """Get enhanced system prompt for farm data analysis."""
        return """Vous êtes un expert en analyse de données d'exploitation agricole française.

VOTRE RÔLE:
- Analyser les données de parcelles, interventions et rendements
- Fournir des insights sur la performance de l'exploitation  
- Recommander des optimisations basées sur les données historiques
- Considérer le contexte agricole français et les réglementations

CAPACITÉS AVANCÉES:
- Compréhension sémantique des requêtes en langage naturel
- Analyse de performance avec benchmarking
- Recommandations d'optimisation contextuelle
- Intégration de connaissances agricoles externes

INSTRUCTIONS:
1. Utilisez l'outil semantic_farm_data_query pour les analyses de données
2. Interprétez les résultats dans le contexte agricole français
3. Fournissez des recommandations pratiques et réalisables
4. Intégrez les bonnes pratiques agricoles dans vos conseils
5. Mentionnez les aspects réglementaires quand pertinent

Répondez en français avec des termes agricoles appropriés."""
    
    def _analyze_message_complexity(self, message: str, context: Dict[str, Any]) -> TaskComplexity:
        """Analyze complexity for farm data queries."""
        message_lower = message.lower()
        
        # Simple data retrieval
        if any(word in message_lower for word in ["combien", "quelle", "superficie", "rendement de"]):
            return TaskComplexity.SIMPLE
        
        # Complex analysis
        elif any(word in message_lower for word in ["analyse", "compare", "optimise", "tendance"]):
            return TaskComplexity.COMPLEX
        
        return TaskComplexity.MODERATE
    
    def _retrieve_domain_knowledge(self, message: str) -> List[str]:
        """Retrieve farm data specific knowledge."""
        return self.knowledge_retriever.retrieve_relevant_knowledge(
            f"données exploitation rendement {message}", top_k=3
        )
    
    def _should_use_tool(self, tool: Any, message: str, context: Dict[str, Any]) -> bool:
        """Determine if data tools are needed."""
        data_indicators = [
            "données", "parcelles", "rendements", "analyse", "performance",
            "comparaison", "historique", "évolution", "optimisation"
        ]
        return any(indicator in message.lower() for indicator in data_indicators)