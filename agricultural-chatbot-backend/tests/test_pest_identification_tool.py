"""
Comprehensive Unit Tests for Enhanced Pest Identification Tool

Tests cover:
- Input validation
- Pest identification logic
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
from app.tools.crop_health_agent.identify_pest_tool_vector_ready import (
    IdentifyPestTool,
    PestIdentification,
    ValidationError
)
from app.config.pest_analysis_config import (
    PestAnalysisConfig,
    PestValidationConfig,
    PestAnalysisConfigManager
)
from app.data.pest_vector_db_interface import (
    PestKnowledge,
    PestSearchResult,
    JSONPestKnowledgeBase
)


class TestPestIdentificationTool:
    """Test suite for the enhanced pest identification tool."""
    
    @pytest.fixture
    def tool(self):
        """Create a test instance of the pest identification tool."""
        return IdentifyPestTool()
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test pest knowledge base"
            },
            "crops": {
                "blé": {
                    "pests": {
                        "puceron": {
                            "scientific_name": "Sitobion avenae",
                            "damage_patterns": ["feuilles_jaunies", "croissance_ralentie"],
                            "pest_indicators": ["pucerons_verts", "fourmis"],
                            "severity": "moderate",
                            "treatment": ["insecticide_systémique"],
                            "prevention": ["rotation_cultures"],
                            "critical_stages": ["tallage"],
                            "economic_threshold": "5-10 pucerons par tige",
                            "monitoring_methods": ["observation_visuelle"]
                        }
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
        assert tool.name == "identify_pest_tool"
        assert tool.description == "Identifie les ravageurs des cultures à partir des symptômes de dégâts avec recherche sémantique"
        assert tool.use_vector_search is False
        assert tool._config_cache is None
        assert tool._validation_cache is None
        assert tool._knowledge_base is None
    
    def test_tool_initialization_with_custom_path(self, temp_knowledge_file):
        """Test tool initialization with custom knowledge base path."""
        tool = IdentifyPestTool(knowledge_base_path=temp_knowledge_file)
        assert tool.knowledge_base_path == temp_knowledge_file
    
    def test_tool_initialization_with_vector_search(self):
        """Test tool initialization with vector search enabled."""
        tool = IdentifyPestTool(use_vector_search=True)
        assert tool.use_vector_search is True
    
    def test_validate_inputs_valid_data(self, tool):
        """Test input validation with valid data."""
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=["feuilles_jaunies", "croissance_ralentie"],
            pest_indicators=["pucerons_verts"]
        )
        assert len(errors) == 0
    
    def test_validate_inputs_missing_crop_type(self, tool):
        """Test input validation with missing crop type."""
        errors = tool._validate_inputs(
            crop_type="",
            damage_symptoms=["feuilles_jaunies"],
            pest_indicators=[]
        )
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_missing_symptoms(self, tool):
        """Test input validation with missing damage symptoms."""
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=[],
            pest_indicators=[]
        )
        assert len(errors) > 0
        assert any(error.field == "damage_symptoms" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_too_many_symptoms(self, tool):
        """Test input validation with too many symptoms."""
        many_symptoms = [f"symptom_{i}" for i in range(25)]  # More than max_symptoms (20)
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=many_symptoms,
            pest_indicators=[]
        )
        assert len(errors) > 0
        assert any(error.field == "damage_symptoms" and error.severity == "warning" for error in errors)
    
    def test_validate_inputs_invalid_symptom_type(self, tool):
        """Test input validation with invalid symptom type."""
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=[123, "valid_symptom"],  # Non-string symptom
            pest_indicators=[]
        )
        assert len(errors) > 0
        assert any("damage_symptoms[0]" in error.field and error.severity == "error" for error in errors)
    
    def test_validate_inputs_short_symptom(self, tool):
        """Test input validation with too short symptom."""
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=["a"],  # Too short
            pest_indicators=[]
        )
        assert len(errors) > 0
        assert any("damage_symptoms[0]" in error.field and error.severity == "error" for error in errors)
    
    def test_validate_inputs_too_many_indicators(self, tool):
        """Test input validation with too many pest indicators."""
        many_indicators = [f"indicator_{i}" for i in range(25)]  # More than max_pest_indicators (20)
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=["feuilles_jaunies"],
            pest_indicators=many_indicators
        )
        assert len(errors) > 0
        assert any(error.field == "pest_indicators" and error.severity == "warning" for error in errors)
    
    def test_get_config_caching(self, tool):
        """Test that configuration is cached after first access."""
        config1 = tool._get_config()
        config2 = tool._get_config()
        assert config1 is config2  # Same instance (cached)
        assert tool._config_cache is not None
    
    def test_get_validation_config_caching(self, tool):
        """Test that validation configuration is cached after first access."""
        config1 = tool._get_validation_config()
        config2 = tool._get_validation_config()
        assert config1 is config2  # Same instance (cached)
        assert tool._validation_cache is not None
    
    def test_analyze_pest_identifications_no_results(self, tool):
        """Test pest identification analysis with no search results."""
        identifications = tool._analyze_pest_identifications([], ["symptom1"], ["indicator1"])
        assert len(identifications) == 0
    
    def test_analyze_pest_identifications_with_results(self, tool):
        """Test pest identification analysis with search results."""
        # Create mock search result
        pest_knowledge = PestKnowledge(
            crop_type="blé",
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            damage_patterns=["feuilles_jaunies", "croissance_ralentie"],
            pest_indicators=["pucerons_verts", "fourmis"],
            treatment=["insecticide_systémique"],
            prevention=["rotation_cultures"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10 pucerons par tige",
            monitoring_methods=["observation_visuelle"]
        )
        
        search_result = PestSearchResult(
            pest_knowledge=pest_knowledge,
            similarity_score=0.8,
            match_type="damage"
        )
        
        identifications = tool._analyze_pest_identifications(
            [search_result],
            ["feuilles_jaunies"],  # Matches damage pattern
            ["pucerons_verts"]     # Matches pest indicator
        )
        
        assert len(identifications) == 1
        identification = identifications[0]
        assert identification.pest_name == "puceron"
        assert identification.scientific_name == "Sitobion avenae"
        assert identification.confidence > 0.3  # Above minimum threshold
        assert "feuilles_jaunies" in identification.damage_patterns_matched
        assert "pucerons_verts" in identification.pest_indicators_matched
    
    def test_calculate_identification_confidence_no_identifications(self, tool):
        """Test confidence calculation with no identifications."""
        confidence = tool._calculate_identification_confidence([])
        assert confidence == "low"
    
    def test_calculate_identification_confidence_high_confidence(self, tool):
        """Test confidence calculation with high confidence identification."""
        identification = PestIdentification(
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            confidence=0.9,  # High confidence
            severity="moderate",
            damage_patterns_matched=["feuilles_jaunies"],
            pest_indicators_matched=["pucerons_verts"],
            treatment_recommendations=["insecticide_systémique"],
            prevention_measures=["rotation_cultures"]
        )
        
        confidence = tool._calculate_identification_confidence([identification])
        assert confidence == "high"
    
    def test_calculate_identification_confidence_moderate_confidence(self, tool):
        """Test confidence calculation with moderate confidence identification."""
        identification = PestIdentification(
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            confidence=0.7,  # Moderate confidence
            severity="moderate",
            damage_patterns_matched=["feuilles_jaunies"],
            pest_indicators_matched=["pucerons_verts"],
            treatment_recommendations=["insecticide_systémique"],
            prevention_measures=["rotation_cultures"]
        )
        
        confidence = tool._calculate_identification_confidence([identification])
        assert confidence == "moderate"
    
    def test_calculate_identification_confidence_low_confidence(self, tool):
        """Test confidence calculation with low confidence identification."""
        identification = PestIdentification(
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            confidence=0.4,  # Low confidence
            severity="moderate",
            damage_patterns_matched=["feuilles_jaunies"],
            pest_indicators_matched=["pucerons_verts"],
            treatment_recommendations=["insecticide_systémique"],
            prevention_measures=["rotation_cultures"]
        )
        
        confidence = tool._calculate_identification_confidence([identification])
        assert confidence == "low"
    
    def test_generate_treatment_recommendations_no_identifications(self, tool):
        """Test treatment recommendations generation with no identifications."""
        recommendations = tool._generate_treatment_recommendations([])
        assert len(recommendations) == 1
        assert "Aucun ravageur identifié" in recommendations[0]
    
    def test_generate_treatment_recommendations_with_identification(self, tool):
        """Test treatment recommendations generation with identification."""
        identification = PestIdentification(
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            confidence=0.8,  # High confidence
            severity="moderate",
            damage_patterns_matched=["feuilles_jaunies"],
            pest_indicators_matched=["pucerons_verts"],
            treatment_recommendations=["insecticide_systémique", "coccinelles"],
            prevention_measures=["rotation_cultures", "variétés_résistantes"],
            critical_stages=["tallage", "montaison"],
            economic_threshold="5-10 pucerons par tige",
            monitoring_methods=["observation_visuelle", "pièges_jaunes"]
        )
        
        recommendations = tool._generate_treatment_recommendations([identification])
        
        assert len(recommendations) > 1
        assert "Ravageur principal: puceron" in recommendations[0]
        assert "Traitements recommandés:" in recommendations
        assert "  • insecticide_systémique" in recommendations
        assert "  • coccinelles" in recommendations
        assert "Mesures préventives:" in recommendations
        assert "  • rotation_cultures" in recommendations
        assert "Seuil économique: 5-10 pucerons par tige" in recommendations
        assert "Méthodes de surveillance:" in recommendations
        assert "Stades critiques: tallage, montaison" in recommendations
    
    def test_generate_treatment_recommendations_low_confidence(self, tool):
        """Test treatment recommendations generation with low confidence identification."""
        identification = PestIdentification(
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            confidence=0.4,  # Low confidence
            severity="moderate",
            damage_patterns_matched=["feuilles_jaunies"],
            pest_indicators_matched=["pucerons_verts"],
            treatment_recommendations=["insecticide_systémique"],
            prevention_measures=["rotation_cultures"]
        )
        
        recommendations = tool._generate_treatment_recommendations([identification])
        
        assert len(recommendations) == 2
        assert "Identification incertaine" in recommendations[0]
        assert "Surveillance accrue des dégâts" in recommendations[1]
    
    @patch('app.tools.crop_health_agent.identify_pest_tool_vector_ready.asyncio.run')
    def test_run_method_success(self, mock_asyncio_run, tool, temp_knowledge_file):
        """Test successful execution of the _run method."""
        # Mock the async search results
        pest_knowledge = PestKnowledge(
            crop_type="blé",
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            damage_patterns=["feuilles_jaunies", "croissance_ralentie"],
            pest_indicators=["pucerons_verts", "fourmis"],
            treatment=["insecticide_systémique"],
            prevention=["rotation_cultures"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10 pucerons par tige",
            monitoring_methods=["observation_visuelle"]
        )
        
        search_result = PestSearchResult(
            pest_knowledge=pest_knowledge,
            similarity_score=0.8,
            match_type="damage"
        )
        
        mock_asyncio_run.return_value = [search_result]
        
        # Create tool with temp knowledge file
        tool = IdentifyPestTool(knowledge_base_path=temp_knowledge_file)
        
        result = tool._run(
            crop_type="blé",
            damage_symptoms=["feuilles_jaunies"],
            pest_indicators=["pucerons_verts"]
        )
        
        result_data = json.loads(result)
        assert "crop_type" in result_data
        assert result_data["crop_type"] == "blé"
        assert "pest_identifications" in result_data
        assert len(result_data["pest_identifications"]) > 0
        assert "treatment_recommendations" in result_data
    
    def test_run_method_validation_errors(self, tool):
        """Test _run method with validation errors."""
        result = tool._run(
            crop_type="",  # Invalid: empty crop type
            damage_symptoms=[],  # Invalid: no symptoms
            pest_indicators=[]
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    def test_run_method_unsupported_crop(self, tool):
        """Test _run method with unsupported crop type."""
        result = tool._run(
            crop_type="unsupported_crop",
            damage_symptoms=["symptom1"],
            pest_indicators=[]
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "not supported" in result_data["error"]
        assert "supported_crops" in result_data
    
    def test_run_method_exception_handling(self, tool):
        """Test _run method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = tool._run(
                crop_type="blé",
                damage_symptoms=["symptom1"],
                pest_indicators=[]
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de l'identification des ravageurs" in result_data["error"]
            assert "error_type" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_success(self, tool, temp_knowledge_file):
        """Test successful execution of the _arun method."""
        # Create tool with temp knowledge file
        tool = IdentifyPestTool(knowledge_base_path=temp_knowledge_file)
        
        # Mock the knowledge base search
        with patch.object(tool, '_search_pest_knowledge', return_value=[]):
            result = await tool._arun(
                crop_type="blé",
                damage_symptoms=["feuilles_jaunies"],
                pest_indicators=["pucerons_verts"]
            )
            
            result_data = json.loads(result)
            assert "error" in result_data  # No knowledge found
            assert "No pest knowledge found" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_arun_method_validation_errors(self, tool):
        """Test _arun method with validation errors."""
        result = await tool._arun(
            crop_type="",  # Invalid: empty crop type
            damage_symptoms=[],  # Invalid: no symptoms
            pest_indicators=[]
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
                crop_type="blé",
                damage_symptoms=["symptom1"],
                pest_indicators=[]
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de l'identification asynchrone" in result_data["error"]
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


class TestPestAnalysisConfig:
    """Test suite for pest analysis configuration."""
    
    def test_pest_analysis_config_defaults(self):
        """Test default values for pest analysis configuration."""
        config = PestAnalysisConfig()
        
        assert config.minimum_confidence == 0.3
        assert config.high_confidence == 0.8
        assert config.moderate_confidence == 0.6
        assert config.damage_pattern_weight == 0.6
        assert config.pest_indicator_weight == 0.4
        assert config.damage_match_bonus == 0.1
        assert config.indicator_match_bonus == 0.05
        assert config.max_identifications == 5
        assert config.include_prevention is True
        assert config.include_monitoring is True
        assert config.include_economic_threshold is True
        assert config.min_symptoms == 1
        assert config.max_symptoms == 20
        assert config.supported_crops == ["blé", "maïs", "colza"]
    
    def test_pest_validation_config_defaults(self):
        """Test default values for pest validation configuration."""
        config = PestValidationConfig()
        
        assert config.require_crop_type is True
        assert config.allow_unknown_crops is False
        assert config.require_damage_symptoms is True
        assert config.min_symptom_length == 2
        assert config.max_symptom_length == 100
        assert config.require_pest_indicators is False
        assert config.max_pest_indicators == 20
        assert config.strict_validation is True
        assert config.return_validation_errors is True
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = PestAnalysisConfigManager()
        
        assert isinstance(manager.analysis_config, PestAnalysisConfig)
        assert isinstance(manager.validation_config, PestValidationConfig)
    
    def test_config_manager_update_analysis_config(self):
        """Test updating analysis configuration."""
        manager = PestAnalysisConfigManager()
        
        manager.update_analysis_config(minimum_confidence=0.4, max_identifications=10)
        
        assert manager.analysis_config.minimum_confidence == 0.4
        assert manager.analysis_config.max_identifications == 10
    
    def test_config_manager_update_validation_config(self):
        """Test updating validation configuration."""
        manager = PestAnalysisConfigManager()
        
        manager.update_validation_config(strict_validation=False, max_symptoms=30)
        
        assert manager.validation_config.strict_validation is False
        assert manager.validation_config.max_symptoms == 30
    
    def test_config_manager_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        manager = PestAnalysisConfigManager()
        
        # Modify configs
        manager.update_analysis_config(minimum_confidence=0.5)
        manager.update_validation_config(strict_validation=False)
        
        # Reset to defaults
        manager.reset_to_defaults()
        
        assert manager.analysis_config.minimum_confidence == 0.3
        assert manager.validation_config.strict_validation is True


class TestJSONPestKnowledgeBase:
    """Test suite for JSON pest knowledge base."""
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test pest knowledge base"
            },
            "crops": {
                "blé": {
                    "pests": {
                        "puceron": {
                            "scientific_name": "Sitobion avenae",
                            "damage_patterns": ["feuilles_jaunies", "croissance_ralentie"],
                            "pest_indicators": ["pucerons_verts", "fourmis"],
                            "severity": "moderate",
                            "treatment": ["insecticide_systémique"],
                            "prevention": ["rotation_cultures"],
                            "critical_stages": ["tallage"],
                            "economic_threshold": "5-10 pucerons par tige",
                            "monitoring_methods": ["observation_visuelle"]
                        }
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
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        assert kb.knowledge_file_path == temp_knowledge_file
        assert kb._knowledge_cache is None
    
    def test_load_knowledge(self, temp_knowledge_file):
        """Test knowledge loading from file."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        knowledge = kb._load_knowledge()
        
        assert "metadata" in knowledge
        assert "crops" in knowledge
        assert "blé" in knowledge["crops"]
        assert "pests" in knowledge["crops"]["blé"]
        assert "puceron" in knowledge["crops"]["blé"]["pests"]
    
    def test_load_knowledge_caching(self, temp_knowledge_file):
        """Test that knowledge is cached after loading."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        # First load
        knowledge1 = kb._load_knowledge()
        
        # Second load should return cached version
        knowledge2 = kb._load_knowledge()
        
        assert knowledge1 is knowledge2  # Same instance (cached)
        assert kb._knowledge_cache is not None
    
    def test_load_knowledge_file_not_found(self):
        """Test knowledge loading when file doesn't exist."""
        kb = JSONPestKnowledgeBase("nonexistent_file.json")
        knowledge = kb._load_knowledge()
        
        assert knowledge == {}  # Empty dict on error
    
    @pytest.mark.asyncio
    async def test_search_by_damage_patterns(self, temp_knowledge_file):
        """Test searching by damage patterns."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_damage_patterns(
            damage_patterns=["feuilles_jaunies"],
            crop_type="blé",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.pest_knowledge.pest_name == "puceron"
        assert result.pest_knowledge.crop_type == "blé"
        assert result.similarity_score > 0
        assert result.match_type == "damage"
    
    @pytest.mark.asyncio
    async def test_search_by_pest_indicators(self, temp_knowledge_file):
        """Test searching by pest indicators."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_pest_indicators(
            pest_indicators=["pucerons_verts"],
            crop_type="blé",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.pest_knowledge.pest_name == "puceron"
        assert result.pest_knowledge.crop_type == "blé"
        assert result.similarity_score > 0
        assert result.match_type == "indicator"
    
    @pytest.mark.asyncio
    async def test_get_crop_pests(self, temp_knowledge_file):
        """Test getting all pests for a crop."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        pests = await kb.get_crop_pests("blé")
        
        assert len(pests) == 1
        pest = pests[0]
        assert pest.pest_name == "puceron"
        assert pest.crop_type == "blé"
        assert pest.scientific_name == "Sitobion avenae"
        assert pest.severity == "moderate"
    
    @pytest.mark.asyncio
    async def test_get_crop_pests_unknown_crop(self, temp_knowledge_file):
        """Test getting pests for unknown crop."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        pests = await kb.get_crop_pests("unknown_crop")
        
        assert len(pests) == 0
    
    @pytest.mark.asyncio
    async def test_add_pest_knowledge_not_supported(self, temp_knowledge_file):
        """Test that adding pest knowledge is not supported in JSON mode."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        pest_knowledge = PestKnowledge(
            crop_type="test",
            pest_name="test_pest",
            scientific_name="Test pest",
            damage_patterns=["test_damage"],
            pest_indicators=["test_indicator"],
            treatment=["test_treatment"],
            prevention=["test_prevention"],
            severity="moderate",
            critical_stages=["test_stage"],
            economic_threshold="test_threshold",
            monitoring_methods=["test_method"]
        )
        
        result = await kb.add_pest_knowledge(pest_knowledge)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_pest_knowledge_not_supported(self, temp_knowledge_file):
        """Test that updating pest knowledge is not supported in JSON mode."""
        kb = JSONPestKnowledgeBase(temp_knowledge_file)
        
        result = await kb.update_pest_knowledge("blé", "puceron", {"severity": "high"})
        assert result is False


class TestPestKnowledgeDataStructures:
    """Test suite for pest knowledge data structures."""
    
    def test_pest_knowledge_creation(self):
        """Test PestKnowledge dataclass creation."""
        pest_knowledge = PestKnowledge(
            crop_type="blé",
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            damage_patterns=["feuilles_jaunies"],
            pest_indicators=["pucerons_verts"],
            treatment=["insecticide_systémique"],
            prevention=["rotation_cultures"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10 pucerons par tige",
            monitoring_methods=["observation_visuelle"]
        )
        
        assert pest_knowledge.crop_type == "blé"
        assert pest_knowledge.pest_name == "puceron"
        assert pest_knowledge.scientific_name == "Sitobion avenae"
        assert pest_knowledge.damage_patterns == ["feuilles_jaunies"]
        assert pest_knowledge.pest_indicators == ["pucerons_verts"]
        assert pest_knowledge.treatment == ["insecticide_systémique"]
        assert pest_knowledge.prevention == ["rotation_cultures"]
        assert pest_knowledge.severity == "moderate"
        assert pest_knowledge.critical_stages == ["tallage"]
        assert pest_knowledge.economic_threshold == "5-10 pucerons par tige"
        assert pest_knowledge.monitoring_methods == ["observation_visuelle"]
        assert pest_knowledge.embedding_vector is None
        assert pest_knowledge.metadata is None
    
    def test_pest_search_result_creation(self):
        """Test PestSearchResult dataclass creation."""
        pest_knowledge = PestKnowledge(
            crop_type="blé",
            pest_name="puceron",
            scientific_name="Sitobion avenae",
            damage_patterns=["feuilles_jaunies"],
            pest_indicators=["pucerons_verts"],
            treatment=["insecticide_systémique"],
            prevention=["rotation_cultures"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10 pucerons par tige",
            monitoring_methods=["observation_visuelle"]
        )
        
        search_result = PestSearchResult(
            pest_knowledge=pest_knowledge,
            similarity_score=0.8,
            match_type="damage"
        )
        
        assert search_result.pest_knowledge == pest_knowledge
        assert search_result.similarity_score == 0.8
        assert search_result.match_type == "damage"


class TestValidationError:
    """Test suite for ValidationError data structure."""
    
    def test_validation_error_creation(self):
        """Test ValidationError dataclass creation."""
        error = ValidationError(
            field="crop_type",
            message="Crop type is required",
            severity="error"
        )
        
        assert error.field == "crop_type"
        assert error.message == "Crop type is required"
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
class TestPestToolPerformance:
    """Test suite for performance and edge cases."""
    
    def test_large_symptom_list_handling(self):
        """Test handling of large symptom lists."""
        tool = IdentifyPestTool()
        
        # Create large symptom list (but within limits)
        large_symptoms = [f"symptom_{i}" for i in range(20)]  # Max allowed
        
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=large_symptoms,
            pest_indicators=[]
        )
        
        # Should not have errors for valid large list
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_very_long_symptom_string(self):
        """Test handling of very long symptom strings."""
        tool = IdentifyPestTool()
        
        # Create very long symptom string (but within limits)
        long_symptom = "a" * 100  # Max allowed length
        
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=[long_symptom],
            pest_indicators=[]
        )
        
        # Should not have errors for valid long string
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_unicode_symptom_handling(self):
        """Test handling of unicode characters in symptoms."""
        tool = IdentifyPestTool()
        
        unicode_symptoms = ["feuilles_jaunies", "croissance_ralentie", "symptôme_étrange"]
        
        errors = tool._validate_inputs(
            crop_type="blé",
            damage_symptoms=unicode_symptoms,
            pest_indicators=[]
        )
        
        # Should handle unicode without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        tool = IdentifyPestTool()
        
        errors = tool._validate_inputs(
            crop_type="",  # Empty string
            damage_symptoms=[""],  # Empty string in list
            pest_indicators=[]
        )
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "error" for error in errors)
        assert any("damage_symptoms[0]" in error.field and error.severity == "error" for error in errors)
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        tool = IdentifyPestTool()
        
        errors = tool._validate_inputs(
            crop_type=None,  # None value
            damage_symptoms=None,  # None value
            pest_indicators=None
        )
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "error" for error in errors)
        assert any(error.field == "damage_symptoms" and error.severity == "error" for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
