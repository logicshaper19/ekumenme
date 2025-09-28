"""
Unit tests for Agent Orchestration system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.orchestration import AgentOrchestrator, AgriculturalWorkflowState
from app.agents.base_agent import AgentState
from langchain.schema import HumanMessage, AIMessage


class TestAgentOrchestrator:
    """Test cases for AgentOrchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.orchestration.ChatOpenAI'):
            with patch('app.agents.orchestration.FarmDataManagerAgent'):
                with patch('app.agents.orchestration.RegulatoryComplianceAgent'):
                    with patch('app.agents.orchestration.WeatherIntelligenceAgent'):
                        with patch('app.agents.orchestration.CropHealthMonitorAgent'):
                            with patch('app.agents.orchestration.OperationalPlanningCoordinatorAgent'):
                                with patch('app.agents.orchestration.SustainabilityAnalyticsAgent'):
                                    self.orchestrator = AgentOrchestrator()
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        assert self.orchestrator.workflow is not None
        assert self.orchestrator._agent_selector_llm is None  # Lazy initialization
    
    def test_agent_selector_llm_property(self):
        """Test lazy initialization of agent selector LLM."""
        # Should be None initially
        assert self.orchestrator._agent_selector_llm is None
        
        # Accessing the property should trigger initialization
        with patch('app.agents.orchestration.ChatOpenAI') as mock_chat:
            llm = self.orchestrator.agent_selector_llm
            mock_chat.assert_called_once()
    
    def test_initialize_agents(self):
        """Test agent initialization."""
        # This is called during orchestrator initialization
        # We can verify that the agent registry has agents
        from app.agents.base_agent import agent_registry
        agents = agent_registry.list_agents()
        assert len(agents) == 6
        assert "farm_data_manager" in agents
        assert "regulatory_compliance" in agents
        assert "weather_intelligence" in agents
        assert "crop_health" in agents
        assert "operational_planning" in agents
        assert "sustainability_analytics" in agents
    
    def test_build_workflow(self):
        """Test workflow building."""
        assert self.orchestrator.workflow is not None
        # The workflow should be a compiled StateGraph
        assert hasattr(self.orchestrator.workflow, 'invoke')
    
    @patch('app.agents.orchestration.FrenchAgriculturalPrompts.get_agent_selection_prompt')
    def test_select_agent(self, mock_prompt):
        """Test agent selection."""
        mock_prompt.return_value = "Test selection prompt"
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "farm_data_manager"
        
        with patch.object(self.orchestrator, 'agent_selector_llm', return_value=mock_response):
            state = AgriculturalWorkflowState(
                messages=[HumanMessage(content="Test message")],
                user_id="test_user",
                farm_id="test_farm",
                current_agent=None,
                context={},
                metadata={}
            )
            
            result = self.orchestrator._select_agent(state)
            
            assert result["current_agent"] == "farm_data_manager"
            mock_prompt.assert_called_once()
    
    def test_route_to_agent(self):
        """Test agent routing."""
        state = AgriculturalWorkflowState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="farm_data_manager",
            context={},
            metadata={}
        )
        
        route = self.orchestrator._route_to_agent(state)
        assert route == "farm_data_manager"
        
        # Test default routing
        state["current_agent"] = "unknown_agent"
        route = self.orchestrator._route_to_agent(state)
        assert route == "farm_data_manager"  # Default fallback
    
    def test_execute_agent(self):
        """Test agent execution."""
        # Mock agent
        mock_agent = Mock()
        mock_agent.process_message.return_value = {
            "response": "Test response",
            "agent": "farm_data_manager",
            "metadata": {}
        }
        
        with patch('app.agents.base_agent.agent_registry.get_agent', return_value=mock_agent):
            state = AgriculturalWorkflowState(
                messages=[HumanMessage(content="Test message")],
                user_id="test_user",
                farm_id="test_farm",
                current_agent="farm_data_manager",
                context={},
                metadata={}
            )
            
            result = self.orchestrator._execute_agent("farm_data_manager", state)
            
            assert result["agent_response"]["response"] == "Test response"
            mock_agent.process_message.assert_called_once()
    
    def test_execute_agent_error(self):
        """Test agent execution with error."""
        # Mock agent that raises exception
        mock_agent = Mock()
        mock_agent.process_message.side_effect = Exception("Test error")
        
        with patch('app.agents.base_agent.agent_registry.get_agent', return_value=mock_agent):
            state = AgriculturalWorkflowState(
                messages=[HumanMessage(content="Test message")],
                user_id="test_user",
                farm_id="test_farm",
                current_agent="farm_data_manager",
                context={},
                metadata={}
            )
            
            result = self.orchestrator._execute_agent("farm_data_manager", state)
            
            assert "error" in result["agent_response"]["metadata"]
            assert "difficulté technique" in result["agent_response"]["response"]
    
    def test_format_final_response(self):
        """Test final response formatting."""
        state = AgriculturalWorkflowState(
            messages=[HumanMessage(content="Test message")],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="farm_data_manager",
            context={},
            metadata={},
            agent_response={
                "response": "Test response",
                "agent": "farm_data_manager",
                "metadata": {"test": "value"}
            }
        )
        
        result = self.orchestrator._format_final_response(state)
        
        assert result["response"] == "Test response"
        assert result["agent"] == "farm_data_manager"
        assert result["metadata"]["test"] == "value"
        assert "timestamp" in result["metadata"]
    
    def test_process_message(self):
        """Test complete message processing workflow."""
        # Mock the workflow invoke method
        mock_final_state = AgriculturalWorkflowState(
            messages=[HumanMessage(content="Test message"), AIMessage(content="Test response")],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="farm_data_manager",
            context={},
            metadata={},
            agent_response={
                "response": "Test response",
                "agent": "farm_data_manager",
                "metadata": {}
            }
        )
        
        with patch.object(self.orchestrator.workflow, 'invoke', return_value=mock_final_state):
            result = self.orchestrator.process_message(
                message="Test message",
                user_id="test_user",
                farm_id="test_farm",
                context={"test": "context"}
            )
            
            assert result["response"] == "Test response"
            assert result["agent"] == "farm_data_manager"
            assert "metadata" in result
    
    def test_get_available_agents(self):
        """Test getting available agents."""
        agents = self.orchestrator.get_available_agents()
        assert len(agents) == 6
        assert "farm_data_manager" in agents
        assert "regulatory_compliance" in agents
        assert "weather_intelligence" in agents
        assert "crop_health" in agents
        assert "operational_planning" in agents
        assert "sustainability_analytics" in agents
    
    def test_get_agent_info(self):
        """Test getting agent information."""
        # Mock agent
        mock_agent = Mock()
        mock_agent.get_info.return_value = {
            "name": "farm_data_manager",
            "description": "Test description",
            "tools": ["tool1", "tool2"]
        }
        
        with patch('app.agents.base_agent.agent_registry.get_agent', return_value=mock_agent):
            info = self.orchestrator.get_agent_info("farm_data_manager")
            
            assert info["name"] == "farm_data_manager"
            assert info["description"] == "Test description"
            assert info["tools"] == ["tool1", "tool2"]
    
    def test_get_agent_info_not_found(self):
        """Test getting info for non-existent agent."""
        with patch('app.agents.base_agent.agent_registry.get_agent', return_value=None):
            info = self.orchestrator.get_agent_info("non_existent_agent")
            assert info is None


class TestAgriculturalWorkflowState:
    """Test cases for AgriculturalWorkflowState."""
    
    def test_workflow_state_creation(self):
        """Test workflow state creation."""
        state = AgriculturalWorkflowState(
            messages=[HumanMessage(content="Test message")],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="farm_data_manager",
            context={"test": "value"},
            metadata={"meta": "data"}
        )
        
        assert len(state["messages"]) == 1
        assert state["user_id"] == "test_user"
        assert state["farm_id"] == "test_farm"
        assert state["current_agent"] == "farm_data_manager"
        assert state["context"]["test"] == "value"
        assert state["metadata"]["meta"] == "data"
        assert state["agent_response"] is None
    
    def test_workflow_state_defaults(self):
        """Test workflow state with defaults."""
        state = AgriculturalWorkflowState(
            messages=[],
            user_id="test_user"
        )
        
        assert state["farm_id"] is None
        assert state["current_agent"] is None
        assert state["context"] == {}
        assert state["metadata"] == {}
        assert state["agent_response"] is None
