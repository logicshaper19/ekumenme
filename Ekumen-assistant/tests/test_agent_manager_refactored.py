"""
Tests for refactored AgentManager.

Tests verify:
1. Demo agents return canned responses
2. Production agents execute actual agent instances
3. Agent instance caching works correctly
4. Async/sync wrappers work correctly
5. Error handling is granular
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.agents.agent_manager import AgentManager, AgentType


class TestAgentManagerRefactored:
    """Test suite for refactored AgentManager."""
    
    @pytest.fixture
    def manager(self):
        """Create AgentManager instance."""
        return AgentManager()
    
    def test_initialization(self, manager):
        """Test AgentManager initializes correctly."""
        assert manager is not None
        assert hasattr(manager, '_agent_instances')
        assert isinstance(manager._agent_instances, dict)
        assert len(manager._agent_instances) == 0  # No instances cached yet
    
    def test_list_available_agents(self, manager):
        """Test listing all available agents."""
        agents = manager.list_available_agents()
        assert len(agents) == 9  # 6 demo + 3 production
        
        agent_types = [agent.agent_type for agent in agents]
        assert AgentType.FARM_DATA in agent_types
        assert AgentType.INTERNET in agent_types
        assert AgentType.SUPPLIER in agent_types
    
    def test_is_demo_agent(self, manager):
        """Test demo agent detection."""
        # Demo agents
        assert manager._is_demo_agent("farm_data") is True
        assert manager._is_demo_agent("weather") is True
        assert manager._is_demo_agent("crop_health") is True
        assert manager._is_demo_agent("planning") is True
        assert manager._is_demo_agent("regulatory") is True
        assert manager._is_demo_agent("sustainability") is True
        
        # Production agents
        assert manager._is_demo_agent("internet") is False
        assert manager._is_demo_agent("supplier") is False
        assert manager._is_demo_agent("market_prices") is False
    
    @pytest.mark.asyncio
    async def test_execute_demo_agent(self, manager):
        """Test executing a demo agent returns canned response."""
        result = await manager.execute_agent("farm_data", "Analyze my farm data")
        
        assert "response" in result
        assert "agent_type" in result
        assert "agent_name" in result
        assert "capabilities" in result
        assert "metadata" in result
        
        # Check metadata indicates it's a demo
        assert result["metadata"]["is_demo"] is True
        
        # Response should be a canned message
        assert "Farm Data" in result["response"] or "données" in result["response"]
    
    @pytest.mark.asyncio
    async def test_execute_production_agent(self, manager):
        """Test executing a production agent calls actual agent."""
        # Mock the InternetAgent
        with patch('app.agents.agent_manager.InternetAgent') as MockInternetAgent:
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value={
                "response": "Test response from internet agent",
                "sources": ["https://example.com"],
                "metadata": {"query": "test"}
            })
            MockInternetAgent.return_value = mock_agent
            
            result = await manager.execute_agent("internet", "Search for wheat prices")
            
            # Verify agent was created and called
            MockInternetAgent.assert_called_once()
            mock_agent.process.assert_called_once()
            
            # Verify response structure
            assert result["response"] == "Test response from internet agent"
            assert result["sources"] == ["https://example.com"]
            assert result["metadata"]["is_demo"] is False
            assert result["metadata"]["query"] == "test"
    
    @pytest.mark.asyncio
    async def test_agent_instance_caching(self, manager):
        """Test that agent instances are cached and reused."""
        with patch('app.agents.agent_manager.InternetAgent') as MockInternetAgent:
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value={
                "response": "Test response",
                "sources": []
            })
            MockInternetAgent.return_value = mock_agent
            
            # Execute agent twice
            await manager.execute_agent("internet", "Query 1")
            await manager.execute_agent("internet", "Query 2")
            
            # Agent should be created only once (cached)
            MockInternetAgent.assert_called_once()
            
            # But process should be called twice
            assert mock_agent.process.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_agent_instance_unknown_type(self, manager):
        """Test creating agent instance with unknown type raises error."""
        with pytest.raises(ValueError, match="Unknown production agent type"):
            await manager._create_agent_instance("unknown_agent")
    
    @pytest.mark.asyncio
    async def test_execute_agent_unknown_type(self, manager):
        """Test executing unknown agent type returns error."""
        result = await manager.execute_agent("unknown_agent", "Test message")
        
        assert "error" in result
        assert "Unknown agent type" in result["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling_configuration_error(self, manager):
        """Test configuration errors are handled correctly."""
        with patch('app.agents.agent_manager.InternetAgent') as MockInternetAgent:
            MockInternetAgent.side_effect = ValueError("Configuration error")
            
            result = await manager.execute_agent("internet", "Test message")
            
            assert "error" in result
            assert result["error_type"] == "configuration"
            assert "Configuration error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling_execution_error(self, manager):
        """Test execution errors are handled correctly."""
        with patch('app.agents.agent_manager.InternetAgent') as MockInternetAgent:
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(side_effect=RuntimeError("Execution failed"))
            MockInternetAgent.return_value = mock_agent
            
            result = await manager.execute_agent("internet", "Test message")
            
            assert "error" in result
            assert result["error_type"] == "execution"
            assert "Execution failed" in result["error"]
    
    def test_execute_agent_sync(self, manager):
        """Test synchronous wrapper works correctly."""
        # Test with demo agent (doesn't require mocking)
        result = manager.execute_agent_sync("farm_data", "Test message")
        
        assert "response" in result
        assert "agent_type" in result
        assert result["metadata"]["is_demo"] is True
    
    def test_cleanup(self, manager):
        """Test cleanup clears agent instances."""
        # Add some mock instances
        manager._agent_instances["internet"] = Mock()
        manager._agent_instances["supplier"] = Mock()
        
        assert len(manager._agent_instances) == 2
        
        # Cleanup
        manager.cleanup()
        
        assert len(manager._agent_instances) == 0
    
    @pytest.mark.asyncio
    async def test_generate_demo_response(self, manager):
        """Test demo response generation."""
        profile = manager.get_agent_profile(AgentType.FARM_DATA)
        response = manager._generate_demo_response(profile, "Test message")
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain agent name or description
        assert "Farm Data" in response or "données" in response
    
    def test_get_agent_capabilities(self, manager):
        """Test getting agent capabilities."""
        capabilities = manager.get_agent_capabilities(AgentType.INTERNET)
        
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
    
    def test_estimate_cost(self, manager):
        """Test cost estimation."""
        cost = manager.estimate_cost(AgentType.INTERNET, request_count=5)
        
        assert isinstance(cost, float)
        assert cost > 0
    
    @pytest.mark.asyncio
    async def test_context_passed_to_agent(self, manager):
        """Test that context is passed to production agents."""
        context = {"user_id": "123", "location": "Paris"}
        
        with patch('app.agents.agent_manager.InternetAgent') as MockInternetAgent:
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value={
                "response": "Test response",
                "sources": []
            })
            MockInternetAgent.return_value = mock_agent
            
            await manager.execute_agent("internet", "Test message", context)
            
            # Verify context was passed to agent
            mock_agent.process.assert_called_once_with("Test message", context)
    
    @pytest.mark.asyncio
    async def test_supplier_agent_creation(self, manager):
        """Test supplier agent can be created and executed."""
        with patch('app.agents.agent_manager.SupplierAgent') as MockSupplierAgent:
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value={
                "response": "Supplier results",
                "sources": []
            })
            MockSupplierAgent.return_value = mock_agent
            
            result = await manager.execute_agent("supplier", "Find fertilizer suppliers")
            
            MockSupplierAgent.assert_called_once()
            assert result["response"] == "Supplier results"
    
    @pytest.mark.asyncio
    async def test_market_prices_agent_uses_internet_agent(self, manager):
        """Test market_prices agent type uses InternetAgent."""
        with patch('app.agents.agent_manager.InternetAgent') as MockInternetAgent:
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value={
                "response": "Market prices",
                "sources": []
            })
            MockInternetAgent.return_value = mock_agent
            
            result = await manager.execute_agent("market_prices", "Wheat prices")
            
            # Should use InternetAgent for market prices
            MockInternetAgent.assert_called_once()
            assert result["response"] == "Market prices"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

