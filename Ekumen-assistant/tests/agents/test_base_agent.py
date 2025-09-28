"""
Unit tests for base agricultural agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.base_agent import BaseAgriculturalAgent, AgentState, AgentRegistry, agent_registry
from app.utils.prompts import FrenchAgriculturalPrompts


class TestAgent(BaseAgriculturalAgent):
    """Test implementation of BaseAgriculturalAgent."""
    
    def get_system_prompt(self, context=None):
        return "Test system prompt"
    
    def process_message(self, message, state, context=None):
        return self.format_response(f"Test response to: {message}")


class TestBaseAgriculturalAgent:
    """Test cases for BaseAgriculturalAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = TestAgent(
            name="test_agent",
            description="Test agent for unit testing",
            system_prompt="Test prompt"
        )
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "test_agent"
        assert self.agent.description == "Test agent for unit testing"
        assert self.agent.system_prompt == "Test prompt"
        assert self.agent.tools == []
        assert self.agent.llm is not None
        assert self.agent.memory is not None
        assert self.agent.entity_memory is not None
    
    def test_get_system_prompt(self):
        """Test system prompt retrieval."""
        context = {"test": "value"}
        prompt = self.agent.get_system_prompt(context)
        assert prompt == "Test system prompt"
    
    def test_process_message(self):
        """Test message processing."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="test_agent",
            context={},
            metadata={}
        )
        
        response = self.agent.process_message("Hello", state)
        
        assert "response" in response
        assert "agent" in response
        assert "metadata" in response
        assert "timestamp" in response
        assert response["agent"] == "test_agent"
        assert "Hello" in response["response"]
    
    def test_format_response(self):
        """Test response formatting."""
        metadata = {"test": "value"}
        response = self.agent.format_response("Test response", metadata)
        
        assert response["response"] == "Test response"
        assert response["agent"] == "test_agent"
        assert response["metadata"] == metadata
        assert "timestamp" in response
    
    def test_clear_memory(self):
        """Test memory clearing."""
        # Add some messages to memory
        self.agent.memory.chat_memory.add_user_message("Test message")
        self.agent.memory.chat_memory.add_ai_message("Test response")
        
        # Clear memory
        self.agent.clear_memory()
        
        # Check that memory is empty
        assert len(self.agent.memory.chat_memory.messages) == 0
    
    def test_get_memory_summary_empty(self):
        """Test memory summary when empty."""
        summary = self.agent.get_memory_summary()
        assert summary == "Aucune conversation précédente."
    
    def test_get_memory_summary_with_messages(self):
        """Test memory summary with messages."""
        # Add messages to memory
        self.agent.memory.chat_memory.add_user_message("User message")
        self.agent.memory.chat_memory.add_ai_message("AI response")
        
        summary = self.agent.get_memory_summary()
        assert "Conversation récente:" in summary
        assert "User message" in summary
        assert "AI response" in summary
    
    def test_validate_context(self):
        """Test context validation."""
        context = {"test": "value"}
        assert self.agent.validate_context(context) is True
    
    def test_str_representation(self):
        """Test string representation."""
        str_repr = str(self.agent)
        assert "test_agent" in str_repr
        assert "Test agent for unit testing" in str_repr


class TestAgentState:
    """Test cases for AgentState."""
    
    def test_agent_state_creation(self):
        """Test AgentState creation."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="test_agent",
            context={"test": "value"},
            metadata={"meta": "data"}
        )
        
        assert state.user_id == "test_user"
        assert state.farm_id == "test_farm"
        assert state.current_agent == "test_agent"
        assert state.context == {"test": "value"}
        assert state.metadata == {"meta": "data"}
        assert state.messages == []
    
    def test_agent_state_defaults(self):
        """Test AgentState with default values."""
        state = AgentState()
        
        assert state.messages == []
        assert state.user_id == ""
        assert state.farm_id is None
        assert state.current_agent == ""
        assert state.context == {}
        assert state.metadata == {}


class TestAgentRegistry:
    """Test cases for AgentRegistry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = AgentRegistry()
        self.test_agent = TestAgent(
            name="test_agent",
            description="Test agent",
            system_prompt="Test prompt"
        )
    
    def test_register_agent(self):
        """Test agent registration."""
        self.registry.register_agent(self.test_agent)
        
        assert "test_agent" in self.registry.agents
        assert self.registry.agents["test_agent"] == self.test_agent
    
    def test_get_agent(self):
        """Test getting registered agent."""
        self.registry.register_agent(self.test_agent)
        
        retrieved_agent = self.registry.get_agent("test_agent")
        assert retrieved_agent == self.test_agent
        
        # Test non-existent agent
        non_existent = self.registry.get_agent("non_existent")
        assert non_existent is None
    
    def test_list_agents(self):
        """Test listing agents."""
        self.registry.register_agent(self.test_agent)
        
        agents = self.registry.list_agents()
        assert "test_agent" in agents
    
    def test_set_default_agent(self):
        """Test setting default agent."""
        self.registry.register_agent(self.test_agent)
        self.registry.set_default_agent("test_agent")
        
        assert self.registry.default_agent == "test_agent"
        
        # Test setting non-existent agent
        with pytest.raises(ValueError):
            self.registry.set_default_agent("non_existent")
    
    def test_get_default_agent(self):
        """Test getting default agent."""
        self.registry.register_agent(self.test_agent)
        self.registry.set_default_agent("test_agent")
        
        default_agent = self.registry.get_default_agent()
        assert default_agent == self.test_agent
        
        # Test when no default is set
        registry_no_default = AgentRegistry()
        assert registry_no_default.get_default_agent() is None


class TestGlobalAgentRegistry:
    """Test cases for global agent registry."""
    
    def test_global_registry_exists(self):
        """Test that global registry exists."""
        assert agent_registry is not None
        assert isinstance(agent_registry, AgentRegistry)
