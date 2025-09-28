"""
Unit tests for Sustainability & Analytics agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.sustainability_agent import SustainabilityAnalyticsAgent, CarbonFootprintTool, SustainabilityAssessmentTool, CertificationAnalysisTool, EconomicAnalysisTool
from app.agents.base_agent import AgentState


class TestCarbonFootprintTool:
    """Test cases for CarbonFootprintTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = CarbonFootprintTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "carbon_footprint_calculation"
        assert "Calculer l'empreinte carbone" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("exploitation_data", "pratiques", "2024")
        assert "Calcul de l'empreinte carbone pour pratiques sur 2024" in result
        assert "émissions CO2" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("exploitation_data", "pratiques", "2024")
        assert "Calcul de l'empreinte carbone pour pratiques sur 2024" in result


class TestSustainabilityAssessmentTool:
    """Test cases for SustainabilityAssessmentTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SustainabilityAssessmentTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "sustainability_assessment"
        assert "Évaluer les indicateurs de durabilité agricole" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("pratiques", "environnement", "économique")
        assert "Évaluation de la durabilité: pratiques" in result
        assert "environnement" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("pratiques", "environnement", "économique")
        assert "Évaluation de la durabilité: pratiques" in result


class TestCertificationAnalysisTool:
    """Test cases for CertificationAnalysisTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = CertificationAnalysisTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "certification_analysis"
        assert "Analyser les exigences et bénéfices des certifications" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("HVE", "pratiques", 50.0)
        assert "Analyse de certification HVE pour exploitation de 50.0ha" in result
        assert "exigences" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("HVE", "pratiques", 50.0)
        assert "Analyse de certification HVE pour exploitation de 50.0ha" in result


class TestEconomicAnalysisTool:
    """Test cases for EconomicAnalysisTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = EconomicAnalysisTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "economic_analysis"
        assert "Analyser la performance économique" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("financier", "production", "marché")
        assert "Analyse économique: données financières financier" in result
        assert "production" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("financier", "production", "marché")
        assert "Analyse économique: données financières financier" in result


class TestSustainabilityAnalyticsAgent:
    """Test cases for SustainabilityAnalyticsAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.sustainability_agent.ChatOpenAI'):
            self.agent = SustainabilityAnalyticsAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "sustainability_analytics"
        assert "Conseiller en durabilité agricole français" in self.agent.description
        assert len(self.agent.tools) == 4
        assert any(isinstance(tool, CarbonFootprintTool) for tool in self.agent.tools)
        assert any(isinstance(tool, SustainabilityAssessmentTool) for tool in self.agent.tools)
        assert any(isinstance(tool, CertificationAnalysisTool) for tool in self.agent.tools)
        assert any(isinstance(tool, EconomicAnalysisTool) for tool in self.agent.tools)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        context = {"test": "value"}
        prompt = self.agent.get_system_prompt(context)
        
        assert "Conseiller en durabilité agricole français" in prompt
        assert "durabilité" in prompt
    
    @patch('app.agents.sustainability_agent.FrenchAgriculturalPrompts.get_sustainability_analytics_prompt')
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
                current_agent="sustainability_analytics",
                context={},
                metadata={}
            )
            
            response = self.agent.process_message("Test message", state)
            
            assert response["response"] == "Test response"
            assert response["agent"] == "sustainability_analytics"
            assert "metadata" in response
            assert "timestamp" in response
    
    def test_process_message_error(self):
        """Test message processing with error."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="sustainability_analytics",
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
        # Sustainability agent can work with minimal context
        context = {}
        assert self.agent.validate_context(context) is True
        
        context = {"any_field": "value"}
        assert self.agent.validate_context(context) is True
    
    def test_calculate_carbon_footprint(self):
        """Test carbon footprint calculation."""
        footprint = self.agent.calculate_carbon_footprint("farm_data", "pratiques")
        assert "Calcul de l'empreinte carbone" in footprint
        assert "émissions" in footprint
    
    def test_assess_sustainability(self):
        """Test sustainability assessment."""
        assessment = self.agent.assess_sustainability("pratiques", "environnement")
        assert "Évaluation de la durabilité" in assessment
        assert "score" in assessment
    
    def test_analyze_certification_requirements(self):
        """Test certification requirements analysis."""
        analysis = self.agent.analyze_certification_requirements("HVE", "pratiques")
        assert "Analyse de certification HVE" in analysis
        assert "exigences" in analysis
    
    def test_perform_economic_analysis(self):
        """Test economic analysis."""
        analysis = self.agent.perform_economic_analysis("financier", "production")
        assert "Analyse économique" in analysis
        assert "rentabilité" in analysis
    
    def test_generate_sustainability_report(self):
        """Test sustainability report generation."""
        report = self.agent.generate_sustainability_report("farm_123", "2024")
        assert "Rapport de durabilité pour l'exploitation farm_123" in report
        assert "2024" in report
