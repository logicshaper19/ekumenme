"""
Unit tests for Smart Tool Selector Service.

Tests:
- Intent classification
- Tool relevance scoring
- Tool filtering
- Dependency resolution
"""

import pytest
from app.services.smart_tool_selector_service import (
    SmartToolSelectorService,
    QueryIntent,
    ToolRelevance
)


class TestSmartToolSelectorService:
    """Test suite for Smart Tool Selector Service"""
    
    @pytest.fixture
    def selector(self):
        """Create selector instance for testing"""
        return SmartToolSelectorService()
    
    # Test intent classification
    def test_classify_weather_intent(self, selector):
        """Test weather intent classification"""
        intents = selector._classify_query_intent("Quelle est la météo?")
        assert QueryIntent.WEATHER_FORECAST in intents
    
    def test_classify_disease_intent(self, selector):
        """Test disease intent classification"""
        intents = selector._classify_query_intent("Mes plants ont une maladie")
        assert QueryIntent.DISEASE_DIAGNOSIS in intents
    
    def test_classify_pest_intent(self, selector):
        """Test pest intent classification"""
        intents = selector._classify_query_intent("J'ai des limaces sur mes plants")
        assert QueryIntent.PEST_IDENTIFICATION in intents
    
    def test_classify_regulatory_intent(self, selector):
        """Test regulatory intent classification"""
        intents = selector._classify_query_intent("Quel est le code AMM?")
        assert QueryIntent.REGULATORY_CHECK in intents
    
    def test_classify_planning_intent(self, selector):
        """Test planning intent classification"""
        intents = selector._classify_query_intent("Planification des tâches agricoles")
        assert QueryIntent.PLANNING in intents
    
    def test_classify_multiple_intents(self, selector):
        """Test multiple intent classification"""
        intents = selector._classify_query_intent(
            "Quelle est la météo et quels traitements pour les maladies?"
        )
        assert QueryIntent.WEATHER_FORECAST in intents
        assert QueryIntent.DISEASE_DIAGNOSIS in intents
        assert len(intents) >= 2
    
    # Test tool selection
    def test_select_weather_tools(self, selector):
        """Test weather tool selection"""
        available_tools = [
            "get_weather_data",
            "analyze_weather_risks",
            "diagnose_disease",
            "lookup_amm"
        ]
        
        selected = selector.select_tools(
            "Quelle est la météo?",
            available_tools
        )
        
        assert "get_weather_data" in selected
        assert "diagnose_disease" not in selected  # Should be filtered out
    
    def test_select_disease_tools(self, selector):
        """Test disease diagnosis tool selection"""
        available_tools = [
            "get_weather_data",
            "diagnose_disease",
            "identify_pest",
            "generate_treatment_plan"
        ]
        
        selected = selector.select_tools(
            "Mes plants ont des taches jaunes",
            available_tools
        )
        
        assert "diagnose_disease" in selected
        assert "generate_treatment_plan" in selected  # Dependency
    
    def test_select_pest_tools(self, selector):
        """Test pest identification tool selection"""
        available_tools = [
            "identify_pest",
            "generate_treatment_plan",
            "get_weather_data"
        ]
        
        selected = selector.select_tools(
            "J'ai des limaces",
            available_tools
        )
        
        assert "identify_pest" in selected
        assert "generate_treatment_plan" in selected  # Dependency
    
    # Test tool filtering
    def test_filter_irrelevant_tools(self, selector):
        """Test filtering of irrelevant tools"""
        available_tools = [
            "get_weather_data",
            "diagnose_disease",
            "calculate_carbon_footprint",
            "assess_biodiversity"
        ]
        
        selected = selector.select_tools(
            "Quelle est la météo?",
            available_tools
        )
        
        # Should filter out sustainability tools
        assert "calculate_carbon_footprint" not in selected
        assert "assess_biodiversity" not in selected
    
    def test_filter_count(self, selector):
        """Test filtering reduces tool count"""
        available_tools = [f"tool_{i}" for i in range(20)]
        available_tools.extend([
            "get_weather_data",
            "analyze_weather_risks"
        ])
        
        selected = selector.select_tools(
            "Quelle est la météo?",
            available_tools
        )
        
        # Should significantly reduce tool count
        assert len(selected) < len(available_tools)
        assert len(selected) <= 5  # Should be focused
    
    # Test dependency resolution
    def test_add_treatment_plan_dependency(self, selector):
        """Test treatment plan dependency is added"""
        available_tools = [
            "diagnose_disease",
            "generate_treatment_plan",
            "get_weather_data"
        ]
        
        # Select only diagnose_disease initially
        selected = selector.select_tools(
            "Diagnostic de maladie",
            ["diagnose_disease", "generate_treatment_plan"]
        )
        
        # generate_treatment_plan should be added as dependency
        assert "generate_treatment_plan" in selected
    
    def test_add_planning_cost_dependency(self, selector):
        """Test planning cost dependency is added"""
        selected = selector.select_tools(
            "Calcul des coûts",
            ["generate_planning_tasks", "calculate_planning_costs"]
        )
        
        # generate_planning_tasks should be added as dependency
        assert "generate_planning_tasks" in selected
        assert "calculate_planning_costs" in selected
    
    # Test relevance scoring
    def test_score_high_relevance(self, selector):
        """Test high relevance scoring"""
        intents = [QueryIntent.WEATHER_FORECAST]
        score, reasoning, required = selector._calculate_tool_score(
            "get_weather_data",
            intents,
            "météo",
            None
        )
        
        assert score >= 0.8  # High relevance
        assert required == True
    
    def test_score_low_relevance(self, selector):
        """Test low relevance scoring"""
        intents = [QueryIntent.WEATHER_FORECAST]
        score, reasoning, required = selector._calculate_tool_score(
            "calculate_carbon_footprint",
            intents,
            "météo",
            None
        )
        
        assert score < 0.5  # Low relevance
        assert required == False
    
    def test_score_partial_relevance(self, selector):
        """Test partial relevance scoring"""
        intents = [QueryIntent.WEATHER_FORECAST, QueryIntent.PLANNING]
        score, reasoning, required = selector._calculate_tool_score(
            "identify_intervention_windows",
            intents,
            "planification météo",
            None
        )
        
        assert score > 0.5  # Moderate relevance
    
    # Test keyword matching
    def test_keyword_boost(self, selector):
        """Test keyword matching boosts score"""
        intents = [QueryIntent.WEATHER_FORECAST]
        
        # With keyword match
        score_with_keyword, _, _ = selector._calculate_tool_score(
            "get_weather_data",
            intents,
            "météo prévision",
            None
        )
        
        # Without keyword match
        score_without_keyword, _, _ = selector._calculate_tool_score(
            "get_weather_data",
            intents,
            "information",
            None
        )
        
        assert score_with_keyword > score_without_keyword
    
    # Test explanation generation
    def test_explain_selection(self, selector):
        """Test selection explanation generation"""
        available_tools = ["get_weather_data", "diagnose_disease", "lookup_amm"]
        selected_tools = ["get_weather_data"]
        
        explanation = selector.explain_selection(
            "Quelle est la météo?",
            selected_tools,
            available_tools
        )
        
        assert "weather" in explanation.lower()
        assert "filtered" in explanation.lower()
        assert len(explanation) > 0
    
    # Test edge cases
    def test_empty_available_tools(self, selector):
        """Test empty available tools list"""
        selected = selector.select_tools("météo", [])
        assert len(selected) == 0
    
    def test_no_matching_tools(self, selector):
        """Test no matching tools"""
        available_tools = ["calculate_carbon_footprint", "assess_biodiversity"]
        selected = selector.select_tools("météo", available_tools)
        
        # Should return empty or very few tools
        assert len(selected) <= 1
    
    def test_all_tools_relevant(self, selector):
        """Test all tools relevant"""
        available_tools = [
            "get_weather_data",
            "analyze_weather_risks",
            "identify_intervention_windows"
        ]
        
        selected = selector.select_tools(
            "Analyse météo complète",
            available_tools
        )
        
        # Should select all weather tools
        assert len(selected) == len(available_tools)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

