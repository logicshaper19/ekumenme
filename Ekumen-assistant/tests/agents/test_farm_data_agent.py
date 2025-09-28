"""
Unit tests for Farm Data Manager agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.farm_data_agent import FarmDataManagerAgent, FarmDataTool, ParcelAnalysisTool, YieldAnalysisTool
from app.agents.base_agent import AgentState


class TestFarmDataTool:
    """Test cases for FarmDataTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = FarmDataTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "farm_data_query"
        assert "Interroger les données" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("test query")
        assert "Données de l'exploitation pour: test query" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("test query")
        assert "Données de l'exploitation pour: test query" in result


class TestParcelAnalysisTool:
    """Test cases for ParcelAnalysisTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ParcelAnalysisTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "parcel_analysis"
        assert "Analyser les données d'une parcelle" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("parcel_123")
        assert "Analyse de la parcelle parcel_123" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("parcel_123")
        assert "Analyse de la parcelle parcel_123" in result


class TestYieldAnalysisTool:
    """Test cases for YieldAnalysisTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = YieldAnalysisTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "yield_analysis"
        assert "Analyser les rendements" in self.tool.description
    
    def test_tool_run_with_parcel(self):
        """Test tool execution with parcel ID."""
        result = self.tool._run("blé", "parcel_123")
        assert "Analyse des rendements de blé sur la parcelle parcel_123" in result
    
    def test_tool_run_without_parcel(self):
        """Test tool execution without parcel ID."""
        result = self.tool._run("blé")
        assert "Analyse des rendements de blé sur l'exploitation" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("blé", "parcel_123")
        assert "Analyse des rendements de blé sur la parcelle parcel_123" in result


class TestFarmDataManagerAgent:
    """Test cases for FarmDataManagerAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.farm_data_agent.ChatOpenAI'):
            self.agent = FarmDataManagerAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "farm_data_manager"
        assert "Expert en données d'exploitation agricole française" in self.agent.description
        assert len(self.agent.tools) == 3
        assert any(isinstance(tool, FarmDataTool) for tool in self.agent.tools)
        assert any(isinstance(tool, ParcelAnalysisTool) for tool in self.agent.tools)
        assert any(isinstance(tool, YieldAnalysisTool) for tool in self.agent.tools)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        context = {"farm_info": {"name": "Test Farm", "region": "Test Region"}}
        prompt = self.agent.get_system_prompt(context)
        
        assert "Expert en données d'exploitation agricole française" in prompt
        assert "Test Farm" in prompt
        assert "Test Region" in prompt
    
    def test_get_system_prompt_no_context(self):
        """Test system prompt generation without context."""
        prompt = self.agent.get_system_prompt()
        assert "Expert en données d'exploitation agricole française" in prompt
    
    @patch('app.agents.farm_data_agent.FrenchAgriculturalPrompts.get_farm_data_manager_prompt')
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
                current_agent="farm_data_manager",
                context={},
                metadata={}
            )
            
            response = self.agent.process_message("Test message", state)
            
            assert response["response"] == "Test response"
            assert response["agent"] == "farm_data_manager"
            assert "metadata" in response
            assert "timestamp" in response
    
    def test_process_message_error(self):
        """Test message processing with error."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="farm_data_manager",
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
        # Valid context
        valid_context = {"farm_id": "test_farm"}
        assert self.agent.validate_context(valid_context) is True
        
        # Invalid context (missing farm_id)
        invalid_context = {"other_field": "value"}
        assert self.agent.validate_context(invalid_context) is False
    
    def test_get_farm_summary(self):
        """Test farm summary generation."""
        summary = self.agent.get_farm_summary("test_farm")
        assert "Résumé des données de l'exploitation test_farm" in summary
    
    def test_analyze_parcel_performance(self):
        """Test parcel performance analysis."""
        analysis = self.agent.analyze_parcel_performance("parcel_123")
        assert "Analyse de performance de la parcelle parcel_123" in analysis
    
    def test_get_yield_forecast(self):
        """Test yield forecast generation."""
        forecast = self.agent.get_yield_forecast("blé", "2024")
        assert "Prévision de rendement pour blé en 2024" in forecast
    
    def test_suggest_optimizations(self):
        """Test optimization suggestions."""
        context = {"farm_id": "test_farm"}
        suggestions = self.agent.suggest_optimizations(context)
        assert "Suggestions d'optimisation" in suggestions
