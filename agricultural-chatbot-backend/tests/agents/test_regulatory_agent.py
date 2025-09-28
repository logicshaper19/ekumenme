"""
Unit tests for Regulatory Compliance agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.regulatory_agent import RegulatoryComplianceAgent, AMMLookupTool, ProductComplianceTool, ZNTCalculatorTool
from app.agents.base_agent import AgentState


class TestAMMLookupTool:
    """Test cases for AMMLookupTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = AMMLookupTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "amm_lookup"
        assert "Rechercher des informations sur un produit phytosanitaire" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("AMM123456")
        assert "Informations AMM pour le produit AMM123456" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("AMM123456")
        assert "Informations AMM pour le produit AMM123456" in result


class TestProductComplianceTool:
    """Test cases for ProductComplianceTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ProductComplianceTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "product_compliance_check"
        assert "Vérifier la conformité d'un produit" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("Karate Zeon", "colza", "traitement")
        assert "Vérification de conformité: Karate Zeon sur colza pour traitement" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("Karate Zeon", "colza", "traitement")
        assert "Vérification de conformité: Karate Zeon sur colza pour traitement" in result


class TestZNTCalculatorTool:
    """Test cases for ZNTCalculatorTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ZNTCalculatorTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "znt_calculator"
        assert "Calculer les distances de sécurité (ZNT)" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("Karate Zeon", "pulvérisation", 50.0)
        assert "Calcul ZNT pour Karate Zeon: distance minimale 50.0m des cours d'eau" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("Karate Zeon", "pulvérisation", 50.0)
        assert "Calcul ZNT pour Karate Zeon: distance minimale 50.0m des cours d'eau" in result


class TestRegulatoryComplianceAgent:
    """Test cases for RegulatoryComplianceAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.regulatory_agent.ChatOpenAI'):
            self.agent = RegulatoryComplianceAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "regulatory_compliance"
        assert "Conseiller en conformité réglementaire agricole française" in self.agent.description
        assert len(self.agent.tools) == 3
        assert any(isinstance(tool, AMMLookupTool) for tool in self.agent.tools)
        assert any(isinstance(tool, ProductComplianceTool) for tool in self.agent.tools)
        assert any(isinstance(tool, ZNTCalculatorTool) for tool in self.agent.tools)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        context = {"test": "value"}
        prompt = self.agent.get_system_prompt(context)
        
        assert "Conseiller en conformité réglementaire agricole français" in prompt
        assert "réglementation phytosanitaire" in prompt
    
    @patch('app.agents.regulatory_agent.FrenchAgriculturalPrompts.get_regulatory_compliance_prompt')
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
                current_agent="regulatory_compliance",
                context={},
                metadata={}
            )
            
            response = self.agent.process_message("Test message", state)
            
            assert response["response"] == "Test response"
            assert response["agent"] == "regulatory_compliance"
            assert "metadata" in response
            assert "timestamp" in response
    
    def test_process_message_error(self):
        """Test message processing with error."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="regulatory_compliance",
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
        # Regulatory agent can work with minimal context
        context = {}
        assert self.agent.validate_context(context) is True
        
        context = {"any_field": "value"}
        assert self.agent.validate_context(context) is True
    
    def test_check_product_amm(self):
        """Test AMM check for product."""
        result = self.agent.check_product_amm("Karate Zeon")
        assert "Vérification AMM pour Karate Zeon" in result
    
    def test_get_usage_conditions(self):
        """Test usage conditions retrieval."""
        result = self.agent.get_usage_conditions("Karate Zeon", "colza")
        assert "Conditions d'emploi pour Karate Zeon sur colza" in result
    
    def test_calculate_safety_distances(self):
        """Test safety distance calculation."""
        result = self.agent.calculate_safety_distances("Karate Zeon", "pulvérisation")
        assert "Distances de sécurité pour Karate Zeon en pulvérisation" in result
    
    def test_check_regulatory_updates(self):
        """Test regulatory updates check."""
        result = self.agent.check_regulatory_updates("herbicides")
        assert "Mises à jour réglementaires pour herbicides" in result
