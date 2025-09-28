"""
Unit tests for Crop Health Monitor agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.crop_health_agent import CropHealthMonitorAgent, DiseaseDiagnosisTool, PestIdentificationTool, NutrientDeficiencyTool, TreatmentRecommendationTool
from app.agents.base_agent import AgentState


class TestDiseaseDiagnosisTool:
    """Test cases for DiseaseDiagnosisTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DiseaseDiagnosisTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "disease_diagnosis"
        assert "Diagnostiquer les maladies des cultures" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("blé", "taches jaunes", "Paris")
        assert "Diagnostic pour blé à Paris" in result
        assert "taches jaunes" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("blé", "taches jaunes", "Paris")
        assert "Diagnostic pour blé à Paris" in result


class TestPestIdentificationTool:
    """Test cases for PestIdentificationTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PestIdentificationTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "pest_identification"
        assert "Identifier les ravageurs et insectes nuisibles" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("blé", "petits insectes verts", "feuilles trouées")
        assert "Identification des ravageurs sur blé" in result
        assert "petits insectes verts" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("blé", "petits insectes verts", "feuilles trouées")
        assert "Identification des ravageurs sur blé" in result


class TestNutrientDeficiencyTool:
    """Test cases for NutrientDeficiencyTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = NutrientDeficiencyTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "nutrient_deficiency_analysis"
        assert "Analyser les carences nutritionnelles" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("blé", "feuilles jaunes", "tallage")
        assert "Analyse des carences pour blé au stade tallage" in result
        assert "feuilles jaunes" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("blé", "feuilles jaunes", "tallage")
        assert "Analyse des carences pour blé au stade tallage" in result


class TestTreatmentRecommendationTool:
    """Test cases for TreatmentRecommendationTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = TreatmentRecommendationTool()
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "treatment_recommendation"
        assert "Recommander des traitements" in self.tool.description
    
    def test_tool_run(self):
        """Test tool execution."""
        result = self.tool._run("septoriose", "blé", "modérée", "montaison")
        assert "Recommandations de traitement pour septoriose sur blé" in result
        assert "sévérité: modérée" in result
    
    @pytest.mark.asyncio
    async def test_tool_arun(self):
        """Test async tool execution."""
        result = await self.tool._arun("septoriose", "blé", "modérée", "montaison")
        assert "Recommandations de traitement pour septoriose sur blé" in result


class TestCropHealthMonitorAgent:
    """Test cases for CropHealthMonitorAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.agents.crop_health_agent.ChatOpenAI'):
            self.agent = CropHealthMonitorAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "crop_health"
        assert "Spécialiste de la santé des cultures françaises" in self.agent.description
        assert len(self.agent.tools) == 4
        assert any(isinstance(tool, DiseaseDiagnosisTool) for tool in self.agent.tools)
        assert any(isinstance(tool, PestIdentificationTool) for tool in self.agent.tools)
        assert any(isinstance(tool, NutrientDeficiencyTool) for tool in self.agent.tools)
        assert any(isinstance(tool, TreatmentRecommendationTool) for tool in self.agent.tools)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        context = {"test": "value"}
        prompt = self.agent.get_system_prompt(context)
        
        assert "Spécialiste de la santé des cultures françaises" in prompt
        assert "diagnostic phytosanitaire" in prompt
    
    @patch('app.agents.crop_health_agent.FrenchAgriculturalPrompts.get_crop_health_prompt')
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
                current_agent="crop_health",
                context={},
                metadata={}
            )
            
            response = self.agent.process_message("Test message", state)
            
            assert response["response"] == "Test response"
            assert response["agent"] == "crop_health"
            assert "metadata" in response
            assert "timestamp" in response
    
    def test_process_message_error(self):
        """Test message processing with error."""
        state = AgentState(
            messages=[],
            user_id="test_user",
            farm_id="test_farm",
            current_agent="crop_health",
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
        # Crop health agent can work with minimal context
        context = {}
        assert self.agent.validate_context(context) is True
        
        context = {"any_field": "value"}
        assert self.agent.validate_context(context) is True
    
    def test_diagnose_crop_problem(self):
        """Test crop problem diagnosis."""
        diagnosis = self.agent.diagnose_crop_problem("blé", "taches jaunes", "Paris")
        assert "Diagnostic pour blé à Paris" in diagnosis
        assert "taches jaunes" in diagnosis
    
    def test_identify_pests(self):
        """Test pest identification."""
        identification = self.agent.identify_pests("blé", "petits insectes verts")
        assert "Identification des ravageurs sur blé" in identification
        assert "petits insectes verts" in identification
    
    def test_analyze_nutrient_deficiency(self):
        """Test nutrient deficiency analysis."""
        analysis = self.agent.analyze_nutrient_deficiency("blé", "feuilles jaunes")
        assert "Analyse des carences pour blé" in analysis
        assert "feuilles jaunes" in analysis
    
    def test_recommend_treatment(self):
        """Test treatment recommendations."""
        recommendations = self.agent.recommend_treatment("septoriose", "blé", "modérée")
        assert "Recommandations de traitement pour septoriose sur blé" in recommendations
        assert "modérée" in recommendations
    
    def test_get_disease_forecast(self):
        """Test disease forecast."""
        forecast = self.agent.get_disease_forecast("blé", "Paris", "humide")
        assert "Prévision des maladies pour blé à Paris" in forecast
        assert "humide" in forecast
