"""
Smart Tool Selector Service - Context-aware tool filtering.

Prevents unnecessary tool executions by analyzing query intent and context.

Goal: Reduce tool execution from 10-15s to 3-5s by avoiding unnecessary tools
"""

import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent categories"""
    WEATHER_FORECAST = "weather_forecast"
    DISEASE_DIAGNOSIS = "disease_diagnosis"
    PEST_IDENTIFICATION = "pest_identification"
    REGULATORY_CHECK = "regulatory_check"
    FARM_DATA_ANALYSIS = "farm_data_analysis"
    PLANNING = "planning"
    COST_CALCULATION = "cost_calculation"
    SUSTAINABILITY = "sustainability"
    GENERAL_ADVICE = "general_advice"


@dataclass
class ToolRelevance:
    """Tool relevance score"""
    tool_name: str
    relevance_score: float  # 0.0 to 1.0
    reasoning: str
    required: bool  # Must execute this tool


class SmartToolSelectorService:
    """
    Service for intelligent tool selection based on query intent.
    
    Features:
    - Intent-based tool filtering
    - Context-aware relevance scoring
    - Dependency resolution
    - Minimal tool set selection
    """
    
    def __init__(self):
        # Tool to intent mapping
        self.tool_intents = {
            # Weather tools
            "get_weather_data": [QueryIntent.WEATHER_FORECAST, QueryIntent.PLANNING],
            "analyze_weather_risks": [QueryIntent.WEATHER_FORECAST, QueryIntent.PLANNING],
            "identify_intervention_windows": [QueryIntent.PLANNING, QueryIntent.WEATHER_FORECAST],
            "calculate_evapotranspiration": [QueryIntent.SUSTAINABILITY, QueryIntent.PLANNING],
            
            # Crop health tools
            "diagnose_disease": [QueryIntent.DISEASE_DIAGNOSIS, QueryIntent.GENERAL_ADVICE],
            "identify_pest": [QueryIntent.PEST_IDENTIFICATION, QueryIntent.GENERAL_ADVICE],
            "analyze_nutrient_deficiency": [QueryIntent.DISEASE_DIAGNOSIS, QueryIntent.SUSTAINABILITY],
            "generate_treatment_plan": [QueryIntent.DISEASE_DIAGNOSIS, QueryIntent.PEST_IDENTIFICATION],
            
            # Regulatory tools
            "lookup_amm": [QueryIntent.REGULATORY_CHECK, QueryIntent.DISEASE_DIAGNOSIS],
            "check_regulatory_compliance": [QueryIntent.REGULATORY_CHECK, QueryIntent.PLANNING],
            "get_safety_guidelines": [QueryIntent.REGULATORY_CHECK],
            
            # Farm data tools
            "get_farm_data": [QueryIntent.FARM_DATA_ANALYSIS, QueryIntent.PLANNING],
            "calculate_performance_metrics": [QueryIntent.FARM_DATA_ANALYSIS],
            "benchmark_crop_performance": [QueryIntent.FARM_DATA_ANALYSIS],
            "analyze_trends": [QueryIntent.FARM_DATA_ANALYSIS],
            
            # Planning tools
            "generate_planning_tasks": [QueryIntent.PLANNING],
            "optimize_task_sequence": [QueryIntent.PLANNING],
            "calculate_planning_costs": [QueryIntent.COST_CALCULATION, QueryIntent.PLANNING],
            "analyze_resource_requirements": [QueryIntent.PLANNING],
            
            # Sustainability tools
            "calculate_carbon_footprint": [QueryIntent.SUSTAINABILITY],
            "assess_biodiversity": [QueryIntent.SUSTAINABILITY],
            "analyze_soil_health": [QueryIntent.SUSTAINABILITY, QueryIntent.FARM_DATA_ANALYSIS],
            "assess_water_management": [QueryIntent.SUSTAINABILITY]
        }
        
        # Intent keywords for classification
        self.intent_keywords = {
            QueryIntent.WEATHER_FORECAST: [
                "météo", "temps", "pluie", "température", "prévision",
                "climat", "gel", "sécheresse", "vent"
            ],
            QueryIntent.DISEASE_DIAGNOSIS: [
                "maladie", "champignon", "fongique", "mildiou", "oïdium",
                "rouille", "tache", "symptôme", "diagnostic"
            ],
            QueryIntent.PEST_IDENTIFICATION: [
                "ravageur", "insecte", "limace", "puceron", "chenille",
                "parasite", "nuisible", "attaque"
            ],
            QueryIntent.REGULATORY_CHECK: [
                "amm", "autorisation", "réglementation", "légal", "conformité",
                "produit phyto", "homologation", "interdit"
            ],
            QueryIntent.FARM_DATA_ANALYSIS: [
                "parcelle", "exploitation", "rendement", "performance",
                "analyse", "données", "historique", "statistique"
            ],
            QueryIntent.PLANNING: [
                "planification", "calendrier", "programme", "organisation",
                "tâche", "intervention", "planning", "quand"
            ],
            QueryIntent.COST_CALCULATION: [
                "coût", "prix", "budget", "dépense", "économie",
                "rentabilité", "investissement"
            ],
            QueryIntent.SUSTAINABILITY: [
                "durable", "environnement", "carbone", "biodiversité",
                "écologique", "bio", "impact environnemental"
            ],
            QueryIntent.GENERAL_ADVICE: [
                "comment", "conseil", "recommandation", "aide",
                "meilleure méthode", "stratégie", "solution"
            ]
        }
        
        # Tool dependencies
        self.tool_dependencies = {
            "generate_treatment_plan": ["diagnose_disease", "identify_pest"],
            "calculate_planning_costs": ["generate_planning_tasks"],
            "optimize_task_sequence": ["generate_planning_tasks"],
            "analyze_weather_risks": ["get_weather_data"],
            "identify_intervention_windows": ["get_weather_data"]
        }
        
        logger.info("Initialized Smart Tool Selector Service")
    
    def select_tools(
        self,
        query: str,
        available_tools: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Select relevant tools for the query.
        
        Args:
            query: User query
            available_tools: List of available tool names
            context: Optional context
        
        Returns:
            List of selected tool names (filtered and ordered)
        """
        # Classify query intent
        intents = self._classify_query_intent(query)
        
        logger.info(f"🎯 Detected intents: {[i.value for i in intents]}")
        
        # Score all tools
        tool_scores = self._score_tools(available_tools, intents, query, context)
        
        # Filter tools by relevance threshold
        relevant_tools = [
            ts.tool_name for ts in tool_scores
            if ts.relevance_score >= 0.5 or ts.required
        ]
        
        # Add dependencies
        final_tools = self._add_dependencies(relevant_tools)
        
        # Log filtering results
        filtered_count = len(available_tools) - len(final_tools)
        logger.info(
            f"✂️ Filtered {filtered_count} unnecessary tools "
            f"({len(available_tools)} → {len(final_tools)})"
        )
        
        for ts in tool_scores:
            if ts.tool_name in final_tools:
                logger.debug(f"  ✅ {ts.tool_name}: {ts.relevance_score:.2f} - {ts.reasoning}")
            else:
                logger.debug(f"  ❌ {ts.tool_name}: {ts.relevance_score:.2f} - {ts.reasoning}")
        
        return final_tools
    
    def _classify_query_intent(self, query: str) -> List[QueryIntent]:
        """
        Classify query intent based on keywords.
        
        Returns list of detected intents (can be multiple).
        """
        query_lower = query.lower()
        detected_intents = []
        
        for intent, keywords in self.intent_keywords.items():
            # Check if any keywords match
            if any(keyword in query_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Default to general advice if no specific intent detected
        if not detected_intents:
            detected_intents.append(QueryIntent.GENERAL_ADVICE)
        
        return detected_intents
    
    def _score_tools(
        self,
        tools: List[str],
        intents: List[QueryIntent],
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> List[ToolRelevance]:
        """
        Score each tool's relevance to the query.
        """
        tool_scores = []
        
        for tool_name in tools:
            score, reasoning, required = self._calculate_tool_score(
                tool_name, intents, query, context
            )
            
            tool_scores.append(ToolRelevance(
                tool_name=tool_name,
                relevance_score=score,
                reasoning=reasoning,
                required=required
            ))
        
        # Sort by relevance score (descending)
        tool_scores.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return tool_scores
    
    def _calculate_tool_score(
        self,
        tool_name: str,
        intents: List[QueryIntent],
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> tuple[float, str, bool]:
        """
        Calculate relevance score for a tool.
        
        Returns: (score, reasoning, required)
        """
        # Get tool's supported intents
        tool_intents = self.tool_intents.get(tool_name, [])
        
        # Calculate base score from intent matching
        matching_intents = set(tool_intents) & set(intents)
        
        if not matching_intents:
            return 0.0, "No matching intents", False
        
        # Base score: percentage of query intents this tool supports
        base_score = len(matching_intents) / len(intents)
        
        # Boost score for exact keyword matches
        query_lower = query.lower()
        tool_keywords = self._get_tool_keywords(tool_name)
        
        keyword_matches = sum(1 for kw in tool_keywords if kw in query_lower)
        keyword_boost = min(0.3, keyword_matches * 0.1)
        
        final_score = min(1.0, base_score + keyword_boost)
        
        # Determine if required
        required = final_score >= 0.8 or len(matching_intents) == len(intents)
        
        reasoning = f"Matches {len(matching_intents)}/{len(intents)} intents"
        if keyword_matches > 0:
            reasoning += f", {keyword_matches} keyword matches"
        
        return final_score, reasoning, required
    
    def _get_tool_keywords(self, tool_name: str) -> List[str]:
        """Get keywords associated with a tool"""
        # Extract keywords from tool name
        keywords = tool_name.replace("_", " ").split()
        
        # Add specific keywords per tool
        tool_specific_keywords = {
            "get_weather_data": ["météo", "temps", "prévision"],
            "diagnose_disease": ["maladie", "diagnostic", "symptôme"],
            "identify_pest": ["ravageur", "limace", "insecte"],
            "lookup_amm": ["amm", "produit", "autorisation"],
            "generate_planning_tasks": ["planification", "tâche", "calendrier"],
            "calculate_planning_costs": ["coût", "prix", "budget"]
        }
        
        keywords.extend(tool_specific_keywords.get(tool_name, []))
        
        return keywords
    
    def _add_dependencies(self, tools: List[str]) -> List[str]:
        """
        Add required dependencies for selected tools.
        """
        final_tools = set(tools)
        
        for tool in tools:
            if tool in self.tool_dependencies:
                dependencies = self.tool_dependencies[tool]
                final_tools.update(dependencies)
                logger.debug(f"Added dependencies for {tool}: {dependencies}")
        
        return list(final_tools)
    
    def explain_selection(
        self,
        query: str,
        selected_tools: List[str],
        available_tools: List[str]
    ) -> str:
        """
        Generate human-readable explanation of tool selection.
        """
        intents = self._classify_query_intent(query)
        intent_names = [i.value for i in intents]
        
        explanation = f"Query intents: {', '.join(intent_names)}\n"
        explanation += f"Selected {len(selected_tools)}/{len(available_tools)} tools:\n"
        
        for tool in selected_tools:
            explanation += f"  - {tool}\n"
        
        filtered = set(available_tools) - set(selected_tools)
        if filtered:
            explanation += f"Filtered out {len(filtered)} unnecessary tools:\n"
            for tool in filtered:
                explanation += f"  - {tool}\n"
        
        return explanation

