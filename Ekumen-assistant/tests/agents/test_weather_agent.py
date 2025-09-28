"""
Unit tests for Weather Intelligence agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.weather_agent import WeatherIntelligenceAgent, WeatherForecastTool, WeatherConditionsTool, InterventionWindowTool, WeatherRiskTool
from app.agents.base_agent import AgentState


class TestWeatherForecastTool:
    """Test cases for WeatherForecastTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = WeatherForecastTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "weather_forecast"
        assert "Obtenir les prévisions météorologiques" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("Paris", 7)
        assert "Prévisions météo pour Paris sur 7 jours" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("Paris", 7)
        assert "Prévisions météo pour Paris sur 7 jours" in result


class TestWeatherConditionsTool:
    """Test cases for WeatherConditionsTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = WeatherConditionsTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "current_weather"
        assert "Vérifier les conditions météorologiques actuelles" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("Paris")
        assert "Conditions actuelles à Paris" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("Paris")
        assert "Conditions actuelles à Paris" in result


class TestInterventionWindowTool:
    """Test cases for InterventionWindowTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = InterventionWindowTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "intervention_window"
        assert "Déterminer les fenêtres d'intervention optimales" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("traitement", "Paris", 5)
        assert "Fenêtres d'intervention pour traitement à Paris" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("traitement", "Paris", 5)
        assert "Fenêtres d'intervention pour traitement à Paris" in result


class TestWeatherRiskTool:
    """Test cases for WeatherRiskTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = WeatherRiskTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "weather_risk_assessment"
        assert "Évaluer les risques météorologiques" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("gel", "Paris", "blé")
        assert "Évaluation des risques gel pour blé à Paris" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("gel", "Paris", "blé")
        assert "Évaluation des risques gel pour blé à Paris" in result


class TestWeatherIntelligenceAgent:
    """Test cases for WeatherIntelligenceAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.weather_agent.ChatOpenAI'):
            self.agent = WeatherIntelligenceAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "weather_intelligence"
        assert "Expert météorologique agricole français" in self.agent.description
        assert len(self.agent.tools) == 4
        assert any(isinstance(tool, WeatherForecastTool) for tool in self.agent.tools)
        assert any(isinstance(tool, WeatherConditionsTool) for tool in self.agent.tools)
        assert any(isinstance(tool, InterventionWindowTool) for tool in self.agent.tools)
        assert any(isinstance(tool, WeatherRiskTool) for tool in self.agent.tools)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        context = {"location": {"coordinates": {"lat": 48.8566, "lon": 2.3522}}}
        prompt = self.agent.get_system_prompt(context)
        
        assert "Expert météorologique agricole français" in prompt
        assert "48.8566" in prompt
        assert "2.3522" in prompt
    
    def test_get_system_prompt_no_context(self):
        """Test system prompt generation without context."""
        prompt = self.agent.get_system_prompt()
        assert "Expert météorologique agricole français" in prompt
    
    @patch('app.agents.weather_agent.FrenchAgriculturalPrompts.get_weather_intelligence_prompt')
    def test_process_message_success(self, mock_prompt):
        """Test successful message processing."""
        mock_prompt.return_value = "Test system prompt"
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "Test response"
        
        with patch.object(self.agent.llm, 'invoke', return_value=mock_response):
            state = AgentState(
                messages=[],
                user_id="test_user",
                farm_id="test_farm",
                current_agent="weather_intelligence",
                context={},
                metadata={}
            )
            
            response = self.agent.process_message("Test message", state)
            
            assert response["response"] == "Test response"
            assert response["agent"] == "weather_intelligence"
            assert "metadata" in response
            assert "timestamp" in response
    
    def test_process_message_error(self):
        """Test message processing with error."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="weather_intelligence",
            context={},
            metadata={}
        )
        
        # Force an error by mocking LLM to raise exception
        with patch.object(self.agent.llm, 'invoke', side_effect=Exception("Test error")):
            response = self.agent.process_message("Test message", state)
            
            assert "difficulté technique" in response["response"]
            assert "error" in response["metadata"]
    
    def test_validate_context(self):
        """Test context validation."""
        # Valid context with location
        valid_context = {"location": {"coordinates": {"lat": 48.8566, "lon": 2.3522}}}
        assert self.agent.validate_context(valid_context) is True
        
        # Valid context with coordinates
        valid_context2 = {"coordinates": {"lat": 48.8566, "lon": 2.3522}}
        assert self.agent.validate_context(valid_context2) is True
        
        # Invalid context (missing location/coordinates)
        invalid_context = {"other_field": "value"}
        assert self.agent.validate_context(invalid_context) is False
    
    def test_get_weather_summary(self):
        """Test weather summary generation."""
        summary = self.agent.get_weather_summary("Paris", 7)
        assert "Résumé météo pour Paris sur 7 jours" in summary
    
    def test_assess_intervention_conditions(self):
        """Test intervention conditions assessment."""
        assessment = self.agent.assess_intervention_conditions("traitement", "Paris")
        assert "Évaluation des conditions pour traitement à Paris" in assessment
    
    def test_get_weather_alerts(self):
        """Test weather alerts retrieval."""
        alerts = self.agent.get_weather_alerts("Paris")
        assert "Alertes météo pour Paris" in alerts
    
    def test_calculate_evapotranspiration(self):
        """Test evapotranspiration calculation."""
        etp = self.agent.calculate_evapotranspiration("Paris", "blé")
        assert "Calcul ETP pour blé à Paris" in etp
