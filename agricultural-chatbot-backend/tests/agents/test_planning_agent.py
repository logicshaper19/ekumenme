"""
Unit tests for Operational Planning Coordinator agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.planning_agent import OperationalPlanningCoordinatorAgent, WorkPlanningTool, ResourceOptimizationTool, WeatherWindowTool, CostOptimizationTool
from app.agents.base_agent import AgentState


class TestWorkPlanningTool:
    """Test cases for WorkPlanningTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = WorkPlanningTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "work_planning"
        assert "Planifier les travaux agricoles" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("semis", 50.0, "tracteur", "2 semaines")
        assert "Planification des travaux semis sur 50.0ha" in result
        assert "tracteur" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("semis", 50.0, "tracteur", "2 semaines")
        assert "Planification des travaux semis sur 50.0ha" in result


class TestResourceOptimizationTool:
    """Test cases for ResourceOptimizationTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ResourceOptimizationTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "resource_optimization"
        assert "Optimiser l'allocation des ressources" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("tracteur, pulvérisateur", "semis, traitement", "météo")
        assert "Optimisation des ressources: tracteur, pulvérisateur" in result
        assert "semis, traitement" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("tracteur, pulvérisateur", "semis, traitement", "météo")
        assert "Optimisation des ressources: tracteur, pulvérisateur" in result


class TestWeatherWindowTool:
    """Test cases for WeatherWindowTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = WeatherWindowTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "weather_window_analysis"
        assert "Analyser les fenêtres météorologiques optimales" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("traitement", "Paris", 3, "ensoleillé")
        assert "Analyse des fenêtres météo pour traitement à Paris" in result
        assert "3 jours" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("traitement", "Paris", 3, "ensoleillé")
        assert "Analyse des fenêtres météo pour traitement à Paris" in result


class TestCostOptimizationTool:
    """Test cases for CostOptimizationTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = CostOptimizationTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "cost_optimization"
        assert "Optimiser les coûts opérationnels" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("semis", 50.0, 5000.0, "efficacité")
        assert "Optimisation des coûts pour semis sur 50.0ha" in result
        assert "5000.0€" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("semis", 50.0, 5000.0, "efficacité")
        assert "Optimisation des coûts pour semis sur 50.0ha" in result


class TestOperationalPlanningCoordinatorAgent:
    """Test cases for OperationalPlanningCoordinatorAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.planning_agent.ChatOpenAI'):
            self.agent = OperationalPlanningCoordinatorAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "operational_planning"
        assert "Coordinateur de planification opérationnelle agricole français" in self.agent.description
        assert len(self.agent.tools) == 4
        assert any(isinstance(tool, WorkPlanningTool) for tool in self.agent.tools)
        assert any(isinstance(tool, ResourceOptimizationTool) for tool in self.agent.tools)
        assert any(isinstance(tool, WeatherWindowTool) for tool in self.agent.tools)
        assert any(isinstance(tool, CostOptimizationTool) for tool in self.agent.tools)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        context = {"test": "value"}
        prompt = self.agent.get_system_prompt(context)
        
        assert "Coordinateur de planification opérationnelle agricole français" in prompt
        assert "planification" in prompt
    
    @patch('app.agents.planning_agent.FrenchAgriculturalPrompts.get_operational_planning_prompt')
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
                current_agent="operational_planning",
                context={},
                metadata={}
            )
            
            response = self.agent.process_message("Test message", state)
            
            assert response["response"] == "Test response"
            assert response["agent"] == "operational_planning"
            assert "metadata" in response
            assert "timestamp" in response
    
    def test_process_message_error(self):
        """Test message processing with error."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="operational_planning",
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
        # Planning agent can work with minimal context
        context = {}
        assert self.agent.validate_context(context) is True
        
        context = {"any_field": "value"}
        assert self.agent.validate_context(context) is True
    
    def test_create_work_plan(self):
        """Test work plan creation."""
        plan = self.agent.create_work_plan("semis", 50.0, "2 semaines")
        assert "Plan de travail pour semis sur 50.0ha" in plan
        assert "2 semaines" in plan
    
    def test_optimize_resource_allocation(self):
        """Test resource allocation optimization."""
        optimization = self.agent.optimize_resource_allocation("tracteur", "semis")
        assert "Optimisation de l'allocation des ressources tracteur" in optimization
        assert "semis" in optimization
    
    def test_analyze_weather_windows(self):
        """Test weather window analysis."""
        analysis = self.agent.analyze_weather_windows("traitement", "Paris", 3)
        assert "Analyse des fenêtres météo pour traitement à Paris" in analysis
        assert "3 jours" in analysis
    
    def test_calculate_operational_costs(self):
        """Test operational cost calculation."""
        costs = self.agent.calculate_operational_costs("semis", 50.0)
        assert "Calcul des coûts opérationnels pour semis sur 50.0ha" in costs
    
    def test_schedule_interventions(self):
        """Test intervention scheduling."""
        schedule = self.agent.schedule_interventions("semis, traitement", "météo")
        assert "Planification des interventions semis, traitement" in schedule
        assert "météo" in schedule
