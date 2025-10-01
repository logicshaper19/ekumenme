"""
Semantic Crop Health Agent
Enhanced crop health agent using semantic tool selection for intelligent diagnosis and treatment recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool

from .semantic_base_agent import SemanticAgriculturalAgent
from ..utils.prompts import FrenchAgriculturalPrompts

# Import available tools
from ..tools.crop_health_agent import (
    diagnose_disease_tool,
    identify_pest_tool,
    analyze_nutrient_deficiency_tool,
    generate_treatment_plan_tool
)

logger = logging.getLogger(__name__)

class SemanticCropHealthAgent(SemanticAgriculturalAgent):
    """
    Semantic Crop Health Agent with intelligent tool selection.

    This agent specializes in crop health diagnosis and monitoring using:
    - Semantic tool selection for disease diagnosis
    - Intelligent pest identification
    - Context-aware treatment recommendations
    - Database-integrated knowledge base
    """

    def __init__(self, **kwargs):
        """Initialize semantic crop health agent."""

        # Initialize crop health tools (all production-ready)
        tools = [
            diagnose_disease_tool,
            identify_pest_tool,
            analyze_nutrient_deficiency_tool,
            generate_treatment_plan_tool
        ]
        
        super().__init__(
            name="semantic_crop_health",
            description="Expert en santé des cultures avec sélection intelligente d'outils",
            tools=tools,
            tool_selection_method="hybrid",  # Use hybrid approach for best results
            tool_selection_threshold=0.5,   # Lower threshold for crop health sensitivity
            max_tools_per_request=2,         # Usually need 1-2 tools for crop health
            **kwargs
        )
        
        logger.info("Initialized Semantic Crop Health Agent")
    
    def get_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get the system prompt for Semantic Crop Health Agent."""
        base_prompt = FrenchAgriculturalPrompts.get_crop_health_prompt(context)
        
        semantic_enhancement = """
        
        🤖 **CAPACITÉS SÉMANTIQUES AVANCÉES**:
        - Sélection intelligente d'outils basée sur l'analyse sémantique
        - Compréhension contextuelle des symptômes et problèmes
        - Recommandations adaptées au contexte spécifique
        - Intégration avec base de connaissances agricoles
        
        📋 **PROCESSUS D'ANALYSE**:
        1. Analyse sémantique de la demande utilisateur
        2. Sélection automatique des outils les plus pertinents
        3. Extraction intelligente des paramètres
        4. Exécution coordonnée des outils sélectionnés
        5. Synthèse des résultats avec recommandations
        
        🎯 **SPÉCIALISATIONS**:
        - Diagnostic de maladies avec recherche sémantique
        - Identification de ravageurs par analyse des dégâts
        - Recommandations de traitement contextualisées
        - Analyse des carences nutritionnelles
        """
        
        return base_prompt + semantic_enhancement
    
    def process_crop_health_query(
        self, 
        query: str, 
        crop_type: Optional[str] = None,
        location: Optional[str] = None,
        environmental_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a crop health query with enhanced context.
        
        Args:
            query: User query about crop health
            crop_type: Specific crop type if known
            location: Farm location
            environmental_conditions: Current environmental conditions
            
        Returns:
            Enhanced response with tool selection details
        """
        # Build enhanced context
        context = {
            "query_type": "crop_health",
            "specialized_agent": True
        }
        
        if crop_type:
            context["crop_type"] = crop_type
        if location:
            context["location"] = location
        if environmental_conditions:
            context["environmental_conditions"] = environmental_conditions
        
        # Create mock agent state for processing
        from .base_agent import AgentState
        state = AgentState(
            user_id="semantic_user",
            farm_id="semantic_farm",
            conversation_id="semantic_conversation"
        )
        
        # Process with semantic selection
        return self.process_message(query, state, context)
    
    def diagnose_with_semantic_selection(
        self, 
        symptoms_description: str,
        crop_type: str = "blé",
        environmental_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform diagnosis using semantic tool selection.
        
        Args:
            symptoms_description: Description of observed symptoms
            crop_type: Type of crop affected
            environmental_context: Environmental conditions
            
        Returns:
            Diagnosis results with tool selection metadata
        """
        # Construct diagnostic query
        query = f"Diagnostic de maladie sur {crop_type}: {symptoms_description}"
        
        if environmental_context:
            conditions = []
            if environmental_context.get("humidity") == "high":
                conditions.append("conditions humides")
            if environmental_context.get("temperature") == "high":
                conditions.append("températures élevées")
            if conditions:
                query += f" dans des {' et '.join(conditions)}"
        
        return self.process_crop_health_query(
            query=query,
            crop_type=crop_type,
            environmental_conditions=environmental_context
        )
    
    def identify_pest_with_context(
        self,
        damage_description: str,
        crop_type: str = "blé",
        pest_indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Identify pests using semantic analysis of damage patterns.
        
        Args:
            damage_description: Description of observed damage
            crop_type: Type of crop affected
            pest_indicators: Additional pest indicators observed
            
        Returns:
            Pest identification results with confidence scores
        """
        # Construct pest identification query
        query = f"Identification de ravageur sur {crop_type}: {damage_description}"
        
        if pest_indicators:
            query += f" avec observation de {', '.join(pest_indicators)}"
        
        return self.process_crop_health_query(
            query=query,
            crop_type=crop_type
        )
    
    def get_treatment_recommendations(
        self,
        problem_description: str,
        crop_type: str = "blé",
        severity: str = "modérée",
        growth_stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get treatment recommendations using semantic analysis.
        
        Args:
            problem_description: Description of the crop problem
            crop_type: Type of crop affected
            severity: Severity level of the problem
            growth_stage: Current growth stage of the crop
            
        Returns:
            Treatment recommendations with regulatory compliance
        """
        # Construct treatment query
        query = f"Recommandations de traitement pour {crop_type}: {problem_description}"
        query += f" (sévérité: {severity})"
        
        if growth_stage:
            query += f" au stade {growth_stage}"
        
        return self.process_crop_health_query(
            query=query,
            crop_type=crop_type
        )
    
    def analyze_crop_health_trends(
        self,
        historical_data: List[Dict[str, Any]],
        current_observations: str
    ) -> Dict[str, Any]:
        """
        Analyze crop health trends using historical data and current observations.
        
        Args:
            historical_data: Historical crop health data
            current_observations: Current crop health observations
            
        Returns:
            Trend analysis with predictive insights
        """
        # Construct trend analysis query
        query = f"Analyse des tendances de santé des cultures: {current_observations}"
        
        # Add historical context
        if historical_data:
            recent_issues = [item.get("issue_type", "problème") for item in historical_data[-3:]]
            if recent_issues:
                query += f" (historique récent: {', '.join(recent_issues)})"
        
        context = {
            "analysis_type": "trend_analysis",
            "historical_data": historical_data
        }
        
        return self.process_crop_health_query(
            query=query
        )
    
    def get_preventive_recommendations(
        self,
        crop_type: str,
        season: str,
        risk_factors: List[str]
    ) -> Dict[str, Any]:
        """
        Get preventive recommendations based on crop type, season, and risk factors.
        
        Args:
            crop_type: Type of crop
            season: Current season
            risk_factors: Identified risk factors
            
        Returns:
            Preventive recommendations with timing and methods
        """
        # Construct preventive query
        query = f"Recommandations préventives pour {crop_type} en {season}"
        
        if risk_factors:
            query += f" avec risques identifiés: {', '.join(risk_factors)}"
        
        context = {
            "recommendation_type": "preventive",
            "season": season,
            "risk_factors": risk_factors
        }
        
        return self.process_crop_health_query(
            query=query,
            crop_type=crop_type
        )
    
    def validate_treatment_compatibility(
        self,
        proposed_treatments: List[str],
        crop_type: str,
        current_treatments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate treatment compatibility and regulatory compliance.
        
        Args:
            proposed_treatments: List of proposed treatments
            crop_type: Type of crop
            current_treatments: Currently applied treatments
            
        Returns:
            Compatibility analysis with regulatory status
        """
        # Construct compatibility query
        treatments_str = ', '.join(proposed_treatments)
        query = f"Vérification de compatibilité des traitements {treatments_str} sur {crop_type}"
        
        if current_treatments:
            current_str = ', '.join(current_treatments)
            query += f" avec traitements actuels: {current_str}"
        
        context = {
            "validation_type": "treatment_compatibility",
            "proposed_treatments": proposed_treatments,
            "current_treatments": current_treatments or []
        }
        
        return self.process_crop_health_query(
            query=query,
            crop_type=crop_type
        )
