"""
Comprehensive Unit Tests for Enhanced Treatment Plan Tool

Tests cover:
- Input validation
- Treatment plan generation logic
- Configuration management
- Error handling
- Async functionality
- Vector database interface
- Performance and edge cases
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import os

# Import the enhanced tool and related components
from app.tools.crop_health_agent.generate_treatment_plan_tool_vector_ready import (
    GenerateTreatmentPlanTool,
    TreatmentStep,
    ValidationError
)
from app.config.treatment_plan_config import (
    TreatmentPlanConfig,
    TreatmentValidationConfig,
    TreatmentPlanConfigManager
)
from app.data.treatment_vector_db_interface import (
    TreatmentKnowledge,
    TreatmentSearchResult,
    JSONTreatmentKnowledgeBase
)


class TestTreatmentPlanTool:
    """Test suite for the enhanced treatment plan tool."""
    
    @pytest.fixture
    def tool(self):
        """Create a test instance of the treatment plan tool."""
        return GenerateTreatmentPlanTool()
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test treatment knowledge base"
            },
            "treatments": {
                "disease_treatments": {
                    "fongicide_systémique": {
                        "name": "Fongicide systémique",
                        "category": "disease_control",
                        "cost_per_hectare": 45.0,
                        "effectiveness": "high",
                        "application_method": "pulvérisation",
                        "timing": "préventif_curatif",
                        "safety_class": "moderate",
                        "environmental_impact": "moderate",
                        "target_diseases": ["rouille_jaune", "septoriose"],
                        "target_crops": ["blé", "orge"],
                        "application_conditions": {"temperature_min": 5},
                        "dose_range": {"recommended": "1L/ha"},
                        "waiting_period": "21 jours",
                        "compatibility": ["insecticides"]
                    }
                }
            }
        }
    
    @pytest.fixture
    def temp_knowledge_file(self, sample_knowledge_base):
        """Create a temporary knowledge base file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_knowledge_base, f, ensure_ascii=False)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    def test_tool_initialization(self, tool):
        """Test tool initialization with default parameters."""
        assert tool.name == "generate_treatment_plan_tool"
        assert tool.description == "Génère un plan de traitement complet pour la santé des cultures avec recherche sémantique"
        assert tool.use_vector_search is False
        assert tool._config_cache is None
        assert tool._validation_cache is None
        assert tool._knowledge_base is None
    
    def test_validate_inputs_valid_data(self, tool):
        """Test input validation with valid data."""
        disease_json = json.dumps({"diagnoses": [{"disease_name": "rouille", "confidence": 0.8}]})
        errors = tool._validate_inputs(disease_json, None, None, "blé")
        assert len(errors) == 0
    
    def test_validate_inputs_no_analyses(self, tool):
        """Test input validation with no analyses provided."""
        errors = tool._validate_inputs(None, None, None, None)
        assert len(errors) > 0
        assert any(error.field == "analyses" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_invalid_json(self, tool):
        """Test input validation with invalid JSON."""
        errors = tool._validate_inputs("invalid json", None, None, "blé")
        assert len(errors) > 0
        assert any(error.field == "disease_analysis" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_unsupported_crop(self, tool):
        """Test input validation with unsupported crop type."""
        disease_json = json.dumps({"diagnoses": [{"disease_name": "rouille", "confidence": 0.8}]})
        errors = tool._validate_inputs(disease_json, None, None, "unsupported_crop")
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "warning" for error in errors)
    
    def test_generate_treatment_steps_no_results(self, tool):
        """Test treatment step generation with no search results."""
        steps = tool._generate_treatment_steps([], None, None, None)
        assert len(steps) == 0
    
    def test_generate_treatment_steps_with_results(self, tool):
        """Test treatment step generation with search results."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="fongicide_systémique",
            category="disease_control",
            cost_per_hectare=45.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif_curatif",
            safety_class="moderate",
            environmental_impact="moderate",
            target_diseases=["rouille_jaune"],
            target_pests=[],
            target_nutrients=[],
            target_crops=["blé"],
            application_conditions={},
            dose_range={"recommended": "1L/ha"},
            waiting_period="21 jours",
            compatibility=["insecticides"]
        )
        
        search_result = TreatmentSearchResult(
            treatment_knowledge=treatment_knowledge,
            similarity_score=0.9,
            match_type="disease"
        )
        
        steps = tool._generate_treatment_steps([search_result], None, None, None)
        
        assert len(steps) == 1
        step = steps[0]
        assert step["step_name"] == "Traitement disease_control: fongicide_systémique"
        assert step["cost_estimate"] == 45.0
        assert step["effectiveness"] == "high"
    
    def test_calculate_priority_high_severity(self, tool):
        """Test priority calculation for high severity issues."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="fongicide_systémique",
            category="disease_control",
            cost_per_hectare=45.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif_curatif",
            safety_class="moderate",
            environmental_impact="moderate",
            target_diseases=["rouille_jaune"],
            target_pests=[],
            target_nutrients=[],
            target_crops=["blé"],
            application_conditions={},
            dose_range={"recommended": "1L/ha"},
            waiting_period="21 jours",
            compatibility=["insecticides"]
        )
        
        disease_analysis = {
            "diagnoses": [{
                "disease_name": "rouille_jaune",
                "severity": "high",
                "confidence": 0.9,
                "treatment_recommendations": ["fongicide_systémique"]
            }]
        }
        
        priority = tool._calculate_priority(treatment_knowledge, disease_analysis, None, None)
        assert priority == "high"
    
    def test_determine_timing(self, tool):
        """Test timing determination based on priority."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="test_treatment",
            category="disease_control",
            cost_per_hectare=25.0,
            effectiveness="moderate",
            application_method="pulvérisation",
            timing="préventif",
            safety_class="low",
            environmental_impact="low",
            target_diseases=[],
            target_pests=[],
            target_nutrients=[],
            target_crops=[],
            application_conditions={},
            dose_range={},
            waiting_period="7 jours",
            compatibility=[]
        )
        
        assert tool._determine_timing(treatment_knowledge, "high") == "immédiat"
        assert tool._determine_timing(treatment_knowledge, "moderate") == "prochain_arrosage"
        assert tool._determine_timing(treatment_knowledge, "low") == "planifié"
    
    def test_calculate_treatment_cost(self, tool):
        """Test treatment cost calculation."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="test_treatment",
            category="disease_control",
            cost_per_hectare=50.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif",
            safety_class="low",
            environmental_impact="low",
            target_diseases=[],
            target_pests=[],
            target_nutrients=[],
            target_crops=[],
            application_conditions={},
            dose_range={},
            waiting_period="7 jours",
            compatibility=[]
        )
        
        config = tool._get_config()
        cost = tool._calculate_treatment_cost(treatment_knowledge, config)
        assert cost == 50.0  # 50.0 * 1.0 (cost_multiplier)
    
    def test_determine_effectiveness(self, tool):
        """Test effectiveness determination."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="test_treatment",
            category="disease_control",
            cost_per_hectare=25.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif",
            safety_class="low",
            environmental_impact="low",
            target_diseases=[],
            target_pests=[],
            target_nutrients=[],
            target_crops=[],
            application_conditions={},
            dose_range={},
            waiting_period="7 jours",
            compatibility=[]
        )
        
        assert tool._determine_effectiveness(treatment_knowledge, 0.9) == "high"
        assert tool._determine_effectiveness(treatment_knowledge, 0.7) == "moderate"
        assert tool._determine_effectiveness(treatment_knowledge, 0.5) == "low"
    
    def test_generate_executive_summary(self, tool):
        """Test executive summary generation."""
        treatment_steps = [
            {
                "step_name": "Test Treatment",
                "cost_estimate": 50.0,
                "priority": "high"
            }
        ]
        
        disease_analysis = {
            "diagnoses": [{"disease_name": "rouille", "confidence": 0.8}]
        }
        
        summary = tool._generate_executive_summary(treatment_steps, disease_analysis, None, None)
        
        assert summary["total_issues_identified"] == 1
        assert summary["total_treatments_recommended"] == 1
        assert summary["estimated_total_cost"] == 50.0
        assert summary["priority_level"] == "low"  # Only 1 issue
    
    def test_generate_treatment_schedule(self, tool):
        """Test treatment schedule generation."""
        treatment_steps = [
            {"step_name": "High Priority Treatment", "priority": "high"},
            {"step_name": "Moderate Priority Treatment", "priority": "moderate"},
            {"step_name": "Low Priority Treatment", "priority": "low"}
        ]
        
        schedule = tool._generate_treatment_schedule(treatment_steps)
        
        assert "High Priority Treatment" in schedule["immediate_actions"]
        assert "Moderate Priority Treatment" in schedule["short_term_actions"]
        assert "Low Priority Treatment" in schedule["long_term_actions"]
    
    def test_generate_cost_analysis(self, tool):
        """Test cost analysis generation."""
        treatment_steps = [
            {"treatment_type": "disease_control", "cost_estimate": 30.0},
            {"treatment_type": "pest_control", "cost_estimate": 25.0},
            {"treatment_type": "nutrient_supplement", "cost_estimate": 20.0}
        ]
        
        cost_analysis = tool._generate_cost_analysis(treatment_steps)
        
        assert cost_analysis["total_cost"] == 75.0
        assert cost_analysis["cost_breakdown"]["disease_treatments"] == 30.0
        assert cost_analysis["cost_breakdown"]["pest_treatments"] == 25.0
        assert cost_analysis["cost_breakdown"]["nutrient_treatments"] == 20.0
        assert cost_analysis["cost_per_hectare"] == 7.5  # 75.0 / 10 hectares
    
    def test_generate_monitoring_plan(self, tool):
        """Test monitoring plan generation."""
        treatment_steps = [
            {"treatment_type": "disease_control"},
            {"treatment_type": "pest_control"},
            {"treatment_type": "nutrient_supplement"}
        ]
        
        monitoring_plan = tool._generate_monitoring_plan(treatment_steps)
        
        assert monitoring_plan["monitoring_frequency"] == "quotidien"
        assert "symptômes_maladies" in monitoring_plan["key_indicators"]
        assert "présence_ravageurs" in monitoring_plan["key_indicators"]
        assert "symptômes_carences" in monitoring_plan["key_indicators"]
    
    def test_generate_prevention_measures(self, tool):
        """Test prevention measures generation."""
        treatment_steps = [
            {"treatment_type": "disease_control"},
            {"treatment_type": "pest_control"},
            {"treatment_type": "nutrient_supplement"}
        ]
        
        prevention_measures = tool._generate_prevention_measures(treatment_steps)
        
        assert "Mise en place de mesures préventives" in prevention_measures
        assert "Rotation des cultures" in prevention_measures
        assert "Pièges à phéromones" in prevention_measures
        assert "Analyse régulière du sol" in prevention_measures
    
    @patch('app.tools.crop_health_agent.generate_treatment_plan_tool_vector_ready.asyncio.run')
    def test_run_method_success(self, mock_asyncio_run, tool, temp_knowledge_file):
        """Test successful execution of the _run method."""
        # Mock the async search results
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="fongicide_systémique",
            category="disease_control",
            cost_per_hectare=45.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif_curatif",
            safety_class="moderate",
            environmental_impact="moderate",
            target_diseases=["rouille_jaune"],
            target_pests=[],
            target_nutrients=[],
            target_crops=["blé"],
            application_conditions={},
            dose_range={"recommended": "1L/ha"},
            waiting_period="21 jours",
            compatibility=["insecticides"]
        )
        
        search_result = TreatmentSearchResult(
            treatment_knowledge=treatment_knowledge,
            similarity_score=0.9,
            match_type="disease"
        )
        
        mock_asyncio_run.return_value = [search_result]
        
        # Create tool with temp knowledge file
        tool = GenerateTreatmentPlanTool(knowledge_base_path=temp_knowledge_file)
        
        disease_json = json.dumps({"diagnoses": [{"disease_name": "rouille_jaune", "confidence": 0.8}]})
        
        result = tool._run(
            disease_analysis_json=disease_json,
            crop_type="blé"
        )
        
        result_data = json.loads(result)
        assert "plan_metadata" in result_data
        assert "executive_summary" in result_data
        assert "treatment_steps" in result_data
        assert result_data["plan_metadata"]["crop_type"] == "blé"
    
    def test_run_method_validation_errors(self, tool):
        """Test _run method with validation errors."""
        result = tool._run(
            disease_analysis_json=None,
            pest_analysis_json=None,
            nutrient_analysis_json=None,
            crop_type=None
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    def test_run_method_no_results(self, tool):
        """Test _run method with no search results."""
        with patch.object(tool, '_search_treatment_knowledge', return_value=[]):
            disease_json = json.dumps({"diagnoses": [{"disease_name": "unknown_disease", "confidence": 0.8}]})
            
            result = tool._run(
                disease_analysis_json=disease_json,
                crop_type="blé"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "No treatment recommendations found" in result_data["error"]
            assert "suggestions" in result_data
    
    def test_run_method_exception_handling(self, tool):
        """Test _run method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = tool._run(
                disease_analysis_json="test",
                crop_type="blé"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de la génération du plan de traitement" in result_data["error"]
            assert "error_type" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_success(self, tool, temp_knowledge_file):
        """Test successful execution of the _arun method."""
        # Create tool with temp knowledge file
        tool = GenerateTreatmentPlanTool(knowledge_base_path=temp_knowledge_file)
        
        # Mock the knowledge base search
        with patch.object(tool, '_search_treatment_knowledge', return_value=[]):
            disease_json = json.dumps({"diagnoses": [{"disease_name": "rouille_jaune", "confidence": 0.8}]})
            
            result = await tool._arun(
                disease_analysis_json=disease_json,
                crop_type="blé"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data  # No knowledge found
            assert "No treatment recommendations found" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_arun_method_validation_errors(self, tool):
        """Test _arun method with validation errors."""
        result = await tool._arun(
            disease_analysis_json=None,
            pest_analysis_json=None,
            nutrient_analysis_json=None,
            crop_type=None
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_exception_handling(self, tool):
        """Test _arun method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = await tool._arun(
                disease_analysis_json="test",
                crop_type="blé"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de la génération asynchrone du plan de traitement" in result_data["error"]
            assert "error_type" in result_data
    
    def test_clear_cache(self, tool):
        """Test cache clearing functionality."""
        # Access configs to populate cache
        tool._get_config()
        tool._get_validation_config()
        
        # Verify cache is populated
        assert tool._config_cache is not None
        assert tool._validation_cache is not None
        
        # Clear cache
        tool.clear_cache()
        
        # Verify cache is cleared
        assert tool._config_cache is None
        assert tool._validation_cache is None
        assert tool._knowledge_base is None
    
    def test_enable_vector_search(self, tool):
        """Test vector search enable/disable functionality."""
        # Initially disabled
        assert tool.use_vector_search is False
        
        # Enable vector search
        tool.enable_vector_search(True)
        assert tool.use_vector_search is True
        assert tool._knowledge_base is None  # Should reset knowledge base
        
        # Disable vector search
        tool.enable_vector_search(False)
        assert tool.use_vector_search is False
        assert tool._knowledge_base is None  # Should reset knowledge base


class TestTreatmentPlanConfig:
    """Test suite for treatment plan configuration."""
    
    def test_treatment_plan_config_defaults(self):
        """Test default values for treatment plan configuration."""
        config = TreatmentPlanConfig()
        
        assert config.minimum_confidence == 0.6
        assert config.high_confidence == 0.8
        assert config.moderate_confidence == 0.7
        assert config.disease_weight == 0.4
        assert config.pest_weight == 0.3
        assert config.nutrient_weight == 0.3
        assert config.default_cost == 25.0
        assert config.cost_multiplier == 1.0
        assert config.max_treatment_steps == 20
        assert config.include_cost_analysis is True
        assert config.include_monitoring_plan is True
        assert config.include_prevention_measures is True
        assert config.include_treatment_schedule is True
        assert config.high_priority_threshold == 5
        assert config.moderate_priority_threshold == 2
        assert config.low_priority_threshold == 1
        assert config.high_priority_duration == "3-4 weeks"
        assert config.moderate_priority_duration == "2-3 weeks"
        assert config.low_priority_duration == "1-2 weeks"
        assert config.default_hectares == 10
        assert config.cost_per_hectare_calculation is True
        assert config.default_monitoring_frequency == "quotidien"
        assert config.default_monitoring_duration == "2-4 semaines"
        assert config.require_at_least_one_analysis is True
        assert config.max_analyses == 10
        assert "blé" in config.supported_crops
        assert "maïs" in config.supported_crops
    
    def test_treatment_validation_config_defaults(self):
        """Test default values for treatment validation configuration."""
        config = TreatmentValidationConfig()
        
        assert config.require_disease_analysis is False
        assert config.require_pest_analysis is False
        assert config.require_nutrient_analysis is False
        assert config.require_at_least_one_analysis is True
        assert config.validate_json_format is True
        assert config.max_json_size == 10000
        assert config.require_crop_type is False
        assert config.validate_crop_type is True
        assert config.strict_validation is True
        assert config.return_validation_errors is True
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = TreatmentPlanConfigManager()
        
        assert isinstance(manager.treatment_config, TreatmentPlanConfig)
        assert isinstance(manager.validation_config, TreatmentValidationConfig)
    
    def test_config_manager_update_treatment_config(self):
        """Test updating treatment configuration."""
        manager = TreatmentPlanConfigManager()
        
        manager.update_treatment_config(minimum_confidence=0.7, max_treatment_steps=25)
        
        assert manager.treatment_config.minimum_confidence == 0.7
        assert manager.treatment_config.max_treatment_steps == 25
    
    def test_config_manager_update_validation_config(self):
        """Test updating validation configuration."""
        manager = TreatmentPlanConfigManager()
        
        manager.update_validation_config(strict_validation=False, max_json_size=15000)
        
        assert manager.validation_config.strict_validation is False
        assert manager.validation_config.max_json_size == 15000
    
    def test_config_manager_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        manager = TreatmentPlanConfigManager()
        
        # Modify configs
        manager.update_treatment_config(minimum_confidence=0.8)
        manager.update_validation_config(strict_validation=False)
        
        # Reset to defaults
        manager.reset_to_defaults()
        
        assert manager.treatment_config.minimum_confidence == 0.6
        assert manager.validation_config.strict_validation is True


class TestJSONTreatmentKnowledgeBase:
    """Test suite for JSON treatment knowledge base."""
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test treatment knowledge base"
            },
            "treatments": {
                "disease_treatments": {
                    "fongicide_systémique": {
                        "name": "Fongicide systémique",
                        "category": "disease_control",
                        "cost_per_hectare": 45.0,
                        "effectiveness": "high",
                        "application_method": "pulvérisation",
                        "timing": "préventif_curatif",
                        "safety_class": "moderate",
                        "environmental_impact": "moderate",
                        "target_diseases": ["rouille_jaune"],
                        "target_crops": ["blé"],
                        "application_conditions": {},
                        "dose_range": {"recommended": "1L/ha"},
                        "waiting_period": "21 jours",
                        "compatibility": ["insecticides"]
                    }
                }
            }
        }
    
    @pytest.fixture
    def temp_knowledge_file(self, sample_knowledge_base):
        """Create a temporary knowledge base file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_knowledge_base, f, ensure_ascii=False)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    def test_json_knowledge_base_initialization(self, temp_knowledge_file):
        """Test JSON knowledge base initialization."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        assert kb.knowledge_file_path == temp_knowledge_file
        assert kb._knowledge_cache is None
    
    def test_load_knowledge(self, temp_knowledge_file):
        """Test knowledge loading from file."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        knowledge = kb._load_knowledge()
        
        assert "metadata" in knowledge
        assert "treatments" in knowledge
        assert "disease_treatments" in knowledge["treatments"]
        assert "fongicide_systémique" in knowledge["treatments"]["disease_treatments"]
    
    def test_load_knowledge_caching(self, temp_knowledge_file):
        """Test that knowledge is cached after loading."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        
        # First load
        knowledge1 = kb._load_knowledge()
        
        # Second load should return cached version
        knowledge2 = kb._load_knowledge()
        
        assert knowledge1 is knowledge2  # Same instance (cached)
        assert kb._knowledge_cache is not None
    
    def test_load_knowledge_file_not_found(self):
        """Test knowledge loading when file doesn't exist."""
        kb = JSONTreatmentKnowledgeBase("nonexistent_file.json")
        knowledge = kb._load_knowledge()
        
        assert knowledge == {}  # Empty dict on error
    
    @pytest.mark.asyncio
    async def test_search_by_disease(self, temp_knowledge_file):
        """Test searching by disease."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_disease(
            disease_name="rouille_jaune",
            crop_type="blé",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.treatment_knowledge.treatment_name == "fongicide_systémique"
        assert result.similarity_score > 0
        assert result.match_type == "disease"
    
    @pytest.mark.asyncio
    async def test_search_by_crop(self, temp_knowledge_file):
        """Test searching by crop type."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_crop(
            crop_type="blé",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.treatment_knowledge.treatment_name == "fongicide_systémique"
        assert result.similarity_score > 0
        assert result.match_type == "crop"
    
    @pytest.mark.asyncio
    async def test_get_all_treatments(self, temp_knowledge_file):
        """Test getting all treatments."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        
        treatments = await kb.get_all_treatments()
        
        assert len(treatments) == 1
        treatment = treatments[0]
        assert treatment.treatment_name == "fongicide_systémique"
        assert treatment.category == "disease_control"
        assert treatment.cost_per_hectare == 45.0
        assert treatment.effectiveness == "high"
    
    @pytest.mark.asyncio
    async def test_add_treatment_knowledge_not_supported(self, temp_knowledge_file):
        """Test that adding treatment knowledge is not supported in JSON mode."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="TestTreatment",
            category="test_category",
            cost_per_hectare=25.0,
            effectiveness="moderate",
            application_method="test_method",
            timing="test_timing",
            safety_class="low",
            environmental_impact="low",
            target_diseases=[],
            target_pests=[],
            target_nutrients=[],
            target_crops=[],
            application_conditions={},
            dose_range={},
            waiting_period="7 jours",
            compatibility=[]
        )
        
        result = await kb.add_treatment_knowledge(treatment_knowledge)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_treatment_knowledge_not_supported(self, temp_knowledge_file):
        """Test that updating treatment knowledge is not supported in JSON mode."""
        kb = JSONTreatmentKnowledgeBase(temp_knowledge_file)
        
        result = await kb.update_treatment_knowledge("fongicide_systémique", {"cost_per_hectare": 50.0})
        assert result is False


class TestTreatmentKnowledgeDataStructures:
    """Test suite for treatment knowledge data structures."""
    
    def test_treatment_knowledge_creation(self):
        """Test TreatmentKnowledge dataclass creation."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="fongicide_systémique",
            category="disease_control",
            cost_per_hectare=45.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif_curatif",
            safety_class="moderate",
            environmental_impact="moderate",
            target_diseases=["rouille_jaune"],
            target_pests=[],
            target_nutrients=[],
            target_crops=["blé"],
            application_conditions={},
            dose_range={"recommended": "1L/ha"},
            waiting_period="21 jours",
            compatibility=["insecticides"]
        )
        
        assert treatment_knowledge.treatment_name == "fongicide_systémique"
        assert treatment_knowledge.category == "disease_control"
        assert treatment_knowledge.cost_per_hectare == 45.0
        assert treatment_knowledge.effectiveness == "high"
        assert treatment_knowledge.application_method == "pulvérisation"
        assert treatment_knowledge.timing == "préventif_curatif"
        assert treatment_knowledge.safety_class == "moderate"
        assert treatment_knowledge.environmental_impact == "moderate"
        assert treatment_knowledge.target_diseases == ["rouille_jaune"]
        assert treatment_knowledge.target_pests == []
        assert treatment_knowledge.target_nutrients == []
        assert treatment_knowledge.target_crops == ["blé"]
        assert treatment_knowledge.application_conditions == {}
        assert treatment_knowledge.dose_range == {"recommended": "1L/ha"}
        assert treatment_knowledge.waiting_period == "21 jours"
        assert treatment_knowledge.compatibility == ["insecticides"]
        assert treatment_knowledge.embedding_vector is None
        assert treatment_knowledge.metadata is None
    
    def test_treatment_search_result_creation(self):
        """Test TreatmentSearchResult dataclass creation."""
        treatment_knowledge = TreatmentKnowledge(
            treatment_name="fongicide_systémique",
            category="disease_control",
            cost_per_hectare=45.0,
            effectiveness="high",
            application_method="pulvérisation",
            timing="préventif_curatif",
            safety_class="moderate",
            environmental_impact="moderate",
            target_diseases=["rouille_jaune"],
            target_pests=[],
            target_nutrients=[],
            target_crops=["blé"],
            application_conditions={},
            dose_range={"recommended": "1L/ha"},
            waiting_period="21 jours",
            compatibility=["insecticides"]
        )
        
        search_result = TreatmentSearchResult(
            treatment_knowledge=treatment_knowledge,
            similarity_score=0.9,
            match_type="disease"
        )
        
        assert search_result.treatment_knowledge == treatment_knowledge
        assert search_result.similarity_score == 0.9
        assert search_result.match_type == "disease"


class TestValidationError:
    """Test suite for ValidationError data structure."""
    
    def test_validation_error_creation(self):
        """Test ValidationError dataclass creation."""
        error = ValidationError(
            field="disease_analysis",
            message="Invalid JSON format",
            severity="error"
        )
        
        assert error.field == "disease_analysis"
        assert error.message == "Invalid JSON format"
        assert error.severity == "error"
    
    def test_validation_error_severity_levels(self):
        """Test different severity levels for ValidationError."""
        error_error = ValidationError("field", "message", "error")
        warning_error = ValidationError("field", "message", "warning")
        info_error = ValidationError("field", "message", "info")
        
        assert error_error.severity == "error"
        assert warning_error.severity == "warning"
        assert info_error.severity == "info"


# Performance and Edge Case Tests
class TestTreatmentPlanToolPerformance:
    """Test suite for performance and edge cases."""
    
    def test_large_json_handling(self):
        """Test handling of large JSON inputs."""
        tool = GenerateTreatmentPlanTool()
        
        # Create large JSON (but within limits)
        large_disease_data = {
            "diagnoses": [{"disease_name": f"disease_{i}", "confidence": 0.8} for i in range(100)]
        }
        large_json = json.dumps(large_disease_data)
        
        errors = tool._validate_inputs(large_json, None, None, "blé")
        
        # Should not have errors for valid large JSON
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in inputs."""
        tool = GenerateTreatmentPlanTool()
        
        unicode_data = {
            "diagnoses": [{"disease_name": "rouille_jaune_é", "confidence": 0.8}]
        }
        unicode_json = json.dumps(unicode_data, ensure_ascii=False)
        
        errors = tool._validate_inputs(unicode_json, None, None, "blé")
        
        # Should handle unicode without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        tool = GenerateTreatmentPlanTool()
        
        errors = tool._validate_inputs("", "", "", "")
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "analyses" and error.severity == "error" for error in errors)
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        tool = GenerateTreatmentPlanTool()
        
        errors = tool._validate_inputs(None, None, None, None)
        
        # Should have validation errors for no analyses
        assert len(errors) > 0
        assert any(error.field == "analyses" and error.severity == "error" for error in errors)
    
    def test_complex_analysis_data(self):
        """Test handling of complex analysis data."""
        tool = GenerateTreatmentPlanTool()
        
        complex_data = {
            "diagnoses": [
                {
                    "disease_name": "rouille_jaune_complexe",
                    "confidence": 0.85,
                    "severity": "high",
                    "treatment_recommendations": ["fongicide_systémique", "fongicide_contact"]
                }
            ]
        }
        complex_json = json.dumps(complex_data)
        
        errors = tool._validate_inputs(complex_json, None, None, "blé")
        
        # Should handle complex data without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
