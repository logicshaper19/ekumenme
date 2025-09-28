"""
Comprehensive Unit Tests for Enhanced Disease Diagnosis Tool

Tests cover:
- Input validation
- Disease diagnosis logic
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
from app.tools.crop_health_agent.diagnose_disease_tool_vector_ready import (
    DiagnoseDiseaseTool,
    DiseaseDiagnosis,
    ValidationError
)
from app.config.disease_analysis_config import (
    DiseaseAnalysisConfig,
    DiseaseValidationConfig,
    DiseaseAnalysisConfigManager
)
from app.data.disease_vector_db_interface import (
    DiseaseKnowledge,
    DiseaseSearchResult,
    JSONDiseaseKnowledgeBase
)


class TestDiseaseDiagnosisTool:
    """Test suite for the enhanced disease diagnosis tool."""
    
    @pytest.fixture
    def tool(self):
        """Create a test instance of the disease diagnosis tool."""
        return DiagnoseDiseaseTool()
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test disease knowledge base"
            },
            "crops": {
                "blé": {
                    "diseases": {
                        "rouille_jaune": {
                            "scientific_name": "Puccinia striiformis",
                            "symptoms": ["taches_jaunes", "pustules_jaunes"],
                            "environmental_conditions": {"humidity": "high", "temperature": "moderate"},
                            "severity": "moderate",
                            "treatment": ["fongicide_triazole"],
                            "prevention": ["variétés_résistantes"],
                            "critical_stages": ["tallage"],
                            "economic_threshold": "5-10% de feuilles atteintes",
                            "monitoring_methods": ["observation_visuelle"],
                            "spread_conditions": {"temperature_range": [10, 25]}
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
        assert tool.name == "diagnose_disease_tool"
        assert tool.description == "Diagnostique les maladies des cultures à partir des symptômes avec recherche sémantique"
        assert tool.use_vector_search is False
        assert tool._config_cache is None
        assert tool._validation_cache is None
        assert tool._knowledge_base is None
    
    def test_tool_initialization_with_custom_path(self, temp_knowledge_file):
        """Test tool initialization with custom knowledge base path."""
        tool = DiagnoseDiseaseTool(knowledge_base_path=temp_knowledge_file)
        assert tool.knowledge_base_path == temp_knowledge_file
    
    def test_tool_initialization_with_vector_search(self):
        """Test tool initialization with vector search enabled."""
        tool = DiagnoseDiseaseTool(use_vector_search=True)
        assert tool.use_vector_search is True
    
    def test_validate_inputs_valid_data(self, tool):
        """Test input validation with valid data."""
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=["taches_jaunes", "pustules_jaunes"],
            environmental_conditions={"humidity": 80, "temperature": 20}
        )
        assert len(errors) == 0
    
    def test_validate_inputs_missing_crop_type(self, tool):
        """Test input validation with missing crop type."""
        errors = tool._validate_inputs(
            crop_type="",
            symptoms=["taches_jaunes"],
            environmental_conditions={}
        )
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_missing_symptoms(self, tool):
        """Test input validation with missing symptoms."""
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=[],
            environmental_conditions={}
        )
        assert len(errors) > 0
        assert any(error.field == "symptoms" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_too_many_symptoms(self, tool):
        """Test input validation with too many symptoms."""
        many_symptoms = [f"symptom_{i}" for i in range(25)]  # More than max_symptoms (20)
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=many_symptoms,
            environmental_conditions={}
        )
        assert len(errors) > 0
        assert any(error.field == "symptoms" and error.severity == "warning" for error in errors)
    
    def test_validate_inputs_invalid_symptom_type(self, tool):
        """Test input validation with invalid symptom type."""
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=[123, "valid_symptom"],  # Non-string symptom
            environmental_conditions={}
        )
        assert len(errors) > 0
        assert any("symptoms[0]" in error.field and error.severity == "error" for error in errors)
    
    def test_validate_inputs_short_symptom(self, tool):
        """Test input validation with too short symptom."""
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=["a"],  # Too short
            environmental_conditions={}
        )
        assert len(errors) > 0
        assert any("symptoms[0]" in error.field and error.severity == "error" for error in errors)
    
    def test_validate_inputs_too_many_environmental_conditions(self, tool):
        """Test input validation with too many environmental conditions."""
        many_conditions = {f"condition_{i}": f"value_{i}" for i in range(25)}  # More than max
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=["taches_jaunes"],
            environmental_conditions=many_conditions
        )
        assert len(errors) > 0
        assert any(error.field == "environmental_conditions" and error.severity == "warning" for error in errors)
    
    def test_validate_inputs_invalid_environmental_condition_type(self, tool):
        """Test input validation with invalid environmental condition type."""
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=["taches_jaunes"],
            environmental_conditions={123: "value"}  # Non-string key
        )
        assert len(errors) > 0
        assert any(error.field == "environmental_conditions" and error.severity == "error" for error in errors)
    
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
    
    def test_analyze_disease_diagnoses_no_results(self, tool):
        """Test disease diagnosis analysis with no search results."""
        diagnoses = tool._analyze_disease_diagnoses([], ["symptom1"], {"humidity": 80})
        assert len(diagnoses) == 0
    
    def test_analyze_disease_diagnoses_with_results(self, tool):
        """Test disease diagnosis analysis with search results."""
        # Create mock search result
        disease_knowledge = DiseaseKnowledge(
            crop_type="blé",
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            symptoms=["taches_jaunes", "pustules_jaunes"],
            environmental_conditions={"humidity": "high", "temperature": "moderate"},
            treatment=["fongicide_triazole"],
            prevention=["variétés_résistantes"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10% de feuilles atteintes",
            monitoring_methods=["observation_visuelle"],
            spread_conditions={"temperature_range": [10, 25]}
        )
        
        search_result = DiseaseSearchResult(
            disease_knowledge=disease_knowledge,
            similarity_score=0.8,
            match_type="symptom"
        )
        
        diagnoses = tool._analyze_disease_diagnoses(
            [search_result],
            ["taches_jaunes"],  # Matches symptom
            {"humidity": 80}     # Matches environmental condition
        )
        
        assert len(diagnoses) == 1
        diagnosis = diagnoses[0]
        assert diagnosis.disease_name == "rouille_jaune"
        assert diagnosis.scientific_name == "Puccinia striiformis"
        assert diagnosis.confidence > 0.3  # Above minimum threshold
        assert "taches_jaunes" in diagnosis.symptoms_matched
        assert "humidity" in diagnosis.environmental_conditions_matched
    
    def test_calculate_diagnosis_confidence_no_diagnoses(self, tool):
        """Test confidence calculation with no diagnoses."""
        confidence = tool._calculate_diagnosis_confidence([])
        assert confidence == "low"
    
    def test_calculate_diagnosis_confidence_high_confidence(self, tool):
        """Test confidence calculation with high confidence diagnosis."""
        diagnosis = DiseaseDiagnosis(
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            confidence=0.9,  # High confidence
            severity="moderate",
            symptoms_matched=["taches_jaunes"],
            environmental_conditions_matched=["humidity"],
            treatment_recommendations=["fongicide_triazole"],
            prevention_measures=["variétés_résistantes"]
        )
        
        confidence = tool._calculate_diagnosis_confidence([diagnosis])
        assert confidence == "high"
    
    def test_calculate_diagnosis_confidence_moderate_confidence(self, tool):
        """Test confidence calculation with moderate confidence diagnosis."""
        diagnosis = DiseaseDiagnosis(
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            confidence=0.7,  # Moderate confidence
            severity="moderate",
            symptoms_matched=["taches_jaunes"],
            environmental_conditions_matched=["humidity"],
            treatment_recommendations=["fongicide_triazole"],
            prevention_measures=["variétés_résistantes"]
        )
        
        confidence = tool._calculate_diagnosis_confidence([diagnosis])
        assert confidence == "moderate"
    
    def test_calculate_diagnosis_confidence_low_confidence(self, tool):
        """Test confidence calculation with low confidence diagnosis."""
        diagnosis = DiseaseDiagnosis(
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            confidence=0.4,  # Low confidence
            severity="moderate",
            symptoms_matched=["taches_jaunes"],
            environmental_conditions_matched=["humidity"],
            treatment_recommendations=["fongicide_triazole"],
            prevention_measures=["variétés_résistantes"]
        )
        
        confidence = tool._calculate_diagnosis_confidence([diagnosis])
        assert confidence == "low"
    
    def test_generate_treatment_recommendations_no_diagnoses(self, tool):
        """Test treatment recommendations generation with no diagnoses."""
        recommendations = tool._generate_treatment_recommendations([])
        assert len(recommendations) == 1
        assert "Aucune maladie identifiée" in recommendations[0]
    
    def test_generate_treatment_recommendations_with_diagnosis(self, tool):
        """Test treatment recommendations generation with diagnosis."""
        diagnosis = DiseaseDiagnosis(
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            confidence=0.8,  # High confidence
            severity="moderate",
            symptoms_matched=["taches_jaunes"],
            environmental_conditions_matched=["humidity"],
            treatment_recommendations=["fongicide_triazole", "fongicide_strobilurine"],
            prevention_measures=["variétés_résistantes", "drainage_amélioré"],
            critical_stages=["tallage", "montaison"],
            economic_threshold="5-10% de feuilles atteintes",
            monitoring_methods=["observation_visuelle", "pièges_spores"],
            spread_conditions={"temperature_range": [10, 25]}
        )
        
        recommendations = tool._generate_treatment_recommendations([diagnosis])
        
        assert len(recommendations) > 1
        assert "Diagnostic principal: rouille_jaune" in recommendations[0]
        assert "Traitements recommandés:" in recommendations
        assert "  • fongicide_triazole" in recommendations
        assert "  • fongicide_strobilurine" in recommendations
        assert "Mesures préventives:" in recommendations
        assert "  • variétés_résistantes" in recommendations
        assert "Seuil économique: 5-10% de feuilles atteintes" in recommendations
        assert "Méthodes de surveillance:" in recommendations
        assert "Stades critiques: tallage, montaison" in recommendations
        assert "Conditions de propagation:" in recommendations
    
    def test_generate_treatment_recommendations_low_confidence(self, tool):
        """Test treatment recommendations generation with low confidence diagnosis."""
        diagnosis = DiseaseDiagnosis(
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            confidence=0.4,  # Low confidence
            severity="moderate",
            symptoms_matched=["taches_jaunes"],
            environmental_conditions_matched=["humidity"],
            treatment_recommendations=["fongicide_triazole"],
            prevention_measures=["variétés_résistantes"]
        )
        
        recommendations = tool._generate_treatment_recommendations([diagnosis])
        
        assert len(recommendations) == 2
        assert "Diagnostic incertain" in recommendations[0]
        assert "Surveillance accrue des symptômes" in recommendations[1]
    
    def test_condition_matches(self, tool):
        """Test environmental condition matching logic."""
        # Test humidity conditions
        assert tool._condition_matches("high", 80) is True
        assert tool._condition_matches("moderate", 60) is True
        assert tool._condition_matches("low", 30) is True
        assert tool._condition_matches("very_high", 90) is True
        
        # Test temperature conditions
        assert tool._condition_matches("cool", 15) is True
        assert tool._condition_matches("warm", 30) is True
        
        # Test non-matching conditions
        assert tool._condition_matches("high", 30) is False
        assert tool._condition_matches("cool", 25) is False
    
    @patch('app.tools.crop_health_agent.diagnose_disease_tool_vector_ready.asyncio.run')
    def test_run_method_success(self, mock_asyncio_run, tool, temp_knowledge_file):
        """Test successful execution of the _run method."""
        # Mock the async search results
        disease_knowledge = DiseaseKnowledge(
            crop_type="blé",
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            symptoms=["taches_jaunes", "pustules_jaunes"],
            environmental_conditions={"humidity": "high", "temperature": "moderate"},
            treatment=["fongicide_triazole"],
            prevention=["variétés_résistantes"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10% de feuilles atteintes",
            monitoring_methods=["observation_visuelle"],
            spread_conditions={"temperature_range": [10, 25]}
        )
        
        search_result = DiseaseSearchResult(
            disease_knowledge=disease_knowledge,
            similarity_score=0.8,
            match_type="symptom"
        )
        
        mock_asyncio_run.return_value = [search_result]
        
        # Create tool with temp knowledge file
        tool = DiagnoseDiseaseTool(knowledge_base_path=temp_knowledge_file)
        
        result = tool._run(
            crop_type="blé",
            symptoms=["taches_jaunes"],
            environmental_conditions={"humidity": 80}
        )
        
        result_data = json.loads(result)
        assert "crop_type" in result_data
        assert result_data["crop_type"] == "blé"
        assert "diagnoses" in result_data
        assert len(result_data["diagnoses"]) > 0
        assert "treatment_recommendations" in result_data
    
    def test_run_method_validation_errors(self, tool):
        """Test _run method with validation errors."""
        result = tool._run(
            crop_type="",  # Invalid: empty crop type
            symptoms=[],  # Invalid: no symptoms
            environmental_conditions={}
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    def test_run_method_unsupported_crop(self, tool):
        """Test _run method with unsupported crop type."""
        result = tool._run(
            crop_type="unsupported_crop",
            symptoms=["symptom1"],
            environmental_conditions={}
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
                symptoms=["symptom1"],
                environmental_conditions={}
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors du diagnostic" in result_data["error"]
            assert "error_type" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_success(self, tool, temp_knowledge_file):
        """Test successful execution of the _arun method."""
        # Create tool with temp knowledge file
        tool = DiagnoseDiseaseTool(knowledge_base_path=temp_knowledge_file)
        
        # Mock the knowledge base search
        with patch.object(tool, '_search_disease_knowledge', return_value=[]):
            result = await tool._arun(
                crop_type="blé",
                symptoms=["taches_jaunes"],
                environmental_conditions={"humidity": 80}
            )
            
            result_data = json.loads(result)
            assert "error" in result_data  # No knowledge found
            assert "No disease knowledge found" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_arun_method_validation_errors(self, tool):
        """Test _arun method with validation errors."""
        result = await tool._arun(
            crop_type="",  # Invalid: empty crop type
            symptoms=[],  # Invalid: no symptoms
            environmental_conditions={}
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
                symptoms=["symptom1"],
                environmental_conditions={}
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors du diagnostic asynchrone" in result_data["error"]
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


class TestDiseaseAnalysisConfig:
    """Test suite for disease analysis configuration."""
    
    def test_disease_analysis_config_defaults(self):
        """Test default values for disease analysis configuration."""
        config = DiseaseAnalysisConfig()
        
        assert config.minimum_confidence == 0.3
        assert config.high_confidence == 0.8
        assert config.moderate_confidence == 0.6
        assert config.symptom_weight == 0.7
        assert config.environmental_weight == 0.3
        assert config.symptom_match_bonus == 0.1
        assert config.environmental_match_bonus == 0.05
        assert config.max_diagnoses == 5
        assert config.include_prevention is True
        assert config.include_monitoring is True
        assert config.include_economic_threshold is True
        assert config.include_spread_conditions is True
        assert config.min_symptoms == 1
        assert config.max_symptoms == 20
        assert config.supported_crops == ["blé", "maïs", "colza"]
        assert config.humidity_thresholds["high"] == 80.0
        assert config.temperature_thresholds["cool"] == 20.0
    
    def test_disease_validation_config_defaults(self):
        """Test default values for disease validation configuration."""
        config = DiseaseValidationConfig()
        
        assert config.require_crop_type is True
        assert config.allow_unknown_crops is False
        assert config.require_symptoms is True
        assert config.min_symptom_length == 2
        assert config.max_symptom_length == 100
        assert config.require_environmental_conditions is False
        assert config.max_environmental_conditions == 20
        assert config.validate_environmental_values is True
        assert config.strict_validation is True
        assert config.return_validation_errors is True
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = DiseaseAnalysisConfigManager()
        
        assert isinstance(manager.analysis_config, DiseaseAnalysisConfig)
        assert isinstance(manager.validation_config, DiseaseValidationConfig)
    
    def test_config_manager_update_analysis_config(self):
        """Test updating analysis configuration."""
        manager = DiseaseAnalysisConfigManager()
        
        manager.update_analysis_config(minimum_confidence=0.4, max_diagnoses=10)
        
        assert manager.analysis_config.minimum_confidence == 0.4
        assert manager.analysis_config.max_diagnoses == 10
    
    def test_config_manager_update_validation_config(self):
        """Test updating validation configuration."""
        manager = DiseaseAnalysisConfigManager()
        
        manager.update_validation_config(strict_validation=False, max_symptoms=30)
        
        assert manager.validation_config.strict_validation is False
        assert manager.validation_config.max_symptoms == 30
    
    def test_config_manager_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        manager = DiseaseAnalysisConfigManager()
        
        # Modify configs
        manager.update_analysis_config(minimum_confidence=0.5)
        manager.update_validation_config(strict_validation=False)
        
        # Reset to defaults
        manager.reset_to_defaults()
        
        assert manager.analysis_config.minimum_confidence == 0.3
        assert manager.validation_config.strict_validation is True


class TestJSONDiseaseKnowledgeBase:
    """Test suite for JSON disease knowledge base."""
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test disease knowledge base"
            },
            "crops": {
                "blé": {
                    "diseases": {
                        "rouille_jaune": {
                            "scientific_name": "Puccinia striiformis",
                            "symptoms": ["taches_jaunes", "pustules_jaunes"],
                            "environmental_conditions": {"humidity": "high", "temperature": "moderate"},
                            "severity": "moderate",
                            "treatment": ["fongicide_triazole"],
                            "prevention": ["variétés_résistantes"],
                            "critical_stages": ["tallage"],
                            "economic_threshold": "5-10% de feuilles atteintes",
                            "monitoring_methods": ["observation_visuelle"],
                            "spread_conditions": {"temperature_range": [10, 25]}
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
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        assert kb.knowledge_file_path == temp_knowledge_file
        assert kb._knowledge_cache is None
    
    def test_load_knowledge(self, temp_knowledge_file):
        """Test knowledge loading from file."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        knowledge = kb._load_knowledge()
        
        assert "metadata" in knowledge
        assert "crops" in knowledge
        assert "blé" in knowledge["crops"]
        assert "diseases" in knowledge["crops"]["blé"]
        assert "rouille_jaune" in knowledge["crops"]["blé"]["diseases"]
    
    def test_load_knowledge_caching(self, temp_knowledge_file):
        """Test that knowledge is cached after loading."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        # First load
        knowledge1 = kb._load_knowledge()
        
        # Second load should return cached version
        knowledge2 = kb._load_knowledge()
        
        assert knowledge1 is knowledge2  # Same instance (cached)
        assert kb._knowledge_cache is not None
    
    def test_load_knowledge_file_not_found(self):
        """Test knowledge loading when file doesn't exist."""
        kb = JSONDiseaseKnowledgeBase("nonexistent_file.json")
        knowledge = kb._load_knowledge()
        
        assert knowledge == {}  # Empty dict on error
    
    @pytest.mark.asyncio
    async def test_search_by_symptoms(self, temp_knowledge_file):
        """Test searching by symptoms."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_symptoms(
            symptoms=["taches_jaunes"],
            crop_type="blé",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.disease_knowledge.disease_name == "rouille_jaune"
        assert result.disease_knowledge.crop_type == "blé"
        assert result.similarity_score > 0
        assert result.match_type == "symptom"
    
    @pytest.mark.asyncio
    async def test_search_by_environmental_conditions(self, temp_knowledge_file):
        """Test searching by environmental conditions."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_environmental_conditions(
            environmental_conditions={"humidity": 80},
            crop_type="blé",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.disease_knowledge.disease_name == "rouille_jaune"
        assert result.disease_knowledge.crop_type == "blé"
        assert result.similarity_score > 0
        assert result.match_type == "environmental"
    
    @pytest.mark.asyncio
    async def test_get_crop_diseases(self, temp_knowledge_file):
        """Test getting all diseases for a crop."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        diseases = await kb.get_crop_diseases("blé")
        
        assert len(diseases) == 1
        disease = diseases[0]
        assert disease.disease_name == "rouille_jaune"
        assert disease.crop_type == "blé"
        assert disease.scientific_name == "Puccinia striiformis"
        assert disease.severity == "moderate"
    
    @pytest.mark.asyncio
    async def test_get_crop_diseases_unknown_crop(self, temp_knowledge_file):
        """Test getting diseases for unknown crop."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        diseases = await kb.get_crop_diseases("unknown_crop")
        
        assert len(diseases) == 0
    
    @pytest.mark.asyncio
    async def test_add_disease_knowledge_not_supported(self, temp_knowledge_file):
        """Test that adding disease knowledge is not supported in JSON mode."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        disease_knowledge = DiseaseKnowledge(
            crop_type="test",
            disease_name="test_disease",
            scientific_name="Test disease",
            symptoms=["test_symptom"],
            environmental_conditions={"humidity": "high"},
            treatment=["test_treatment"],
            prevention=["test_prevention"],
            severity="moderate",
            critical_stages=["test_stage"],
            economic_threshold="test_threshold",
            monitoring_methods=["test_method"],
            spread_conditions={"test": "condition"}
        )
        
        result = await kb.add_disease_knowledge(disease_knowledge)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_disease_knowledge_not_supported(self, temp_knowledge_file):
        """Test that updating disease knowledge is not supported in JSON mode."""
        kb = JSONDiseaseKnowledgeBase(temp_knowledge_file)
        
        result = await kb.update_disease_knowledge("blé", "rouille_jaune", {"severity": "high"})
        assert result is False


class TestDiseaseKnowledgeDataStructures:
    """Test suite for disease knowledge data structures."""
    
    def test_disease_knowledge_creation(self):
        """Test DiseaseKnowledge dataclass creation."""
        disease_knowledge = DiseaseKnowledge(
            crop_type="blé",
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            symptoms=["taches_jaunes"],
            environmental_conditions={"humidity": "high"},
            treatment=["fongicide_triazole"],
            prevention=["variétés_résistantes"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10% de feuilles atteintes",
            monitoring_methods=["observation_visuelle"],
            spread_conditions={"temperature_range": [10, 25]}
        )
        
        assert disease_knowledge.crop_type == "blé"
        assert disease_knowledge.disease_name == "rouille_jaune"
        assert disease_knowledge.scientific_name == "Puccinia striiformis"
        assert disease_knowledge.symptoms == ["taches_jaunes"]
        assert disease_knowledge.environmental_conditions == {"humidity": "high"}
        assert disease_knowledge.treatment == ["fongicide_triazole"]
        assert disease_knowledge.prevention == ["variétés_résistantes"]
        assert disease_knowledge.severity == "moderate"
        assert disease_knowledge.critical_stages == ["tallage"]
        assert disease_knowledge.economic_threshold == "5-10% de feuilles atteintes"
        assert disease_knowledge.monitoring_methods == ["observation_visuelle"]
        assert disease_knowledge.spread_conditions == {"temperature_range": [10, 25]}
        assert disease_knowledge.embedding_vector is None
        assert disease_knowledge.metadata is None
    
    def test_disease_search_result_creation(self):
        """Test DiseaseSearchResult dataclass creation."""
        disease_knowledge = DiseaseKnowledge(
            crop_type="blé",
            disease_name="rouille_jaune",
            scientific_name="Puccinia striiformis",
            symptoms=["taches_jaunes"],
            environmental_conditions={"humidity": "high"},
            treatment=["fongicide_triazole"],
            prevention=["variétés_résistantes"],
            severity="moderate",
            critical_stages=["tallage"],
            economic_threshold="5-10% de feuilles atteintes",
            monitoring_methods=["observation_visuelle"],
            spread_conditions={"temperature_range": [10, 25]}
        )
        
        search_result = DiseaseSearchResult(
            disease_knowledge=disease_knowledge,
            similarity_score=0.8,
            match_type="symptom"
        )
        
        assert search_result.disease_knowledge == disease_knowledge
        assert search_result.similarity_score == 0.8
        assert search_result.match_type == "symptom"


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
class TestDiseaseToolPerformance:
    """Test suite for performance and edge cases."""
    
    def test_large_symptom_list_handling(self):
        """Test handling of large symptom lists."""
        tool = DiagnoseDiseaseTool()
        
        # Create large symptom list (but within limits)
        large_symptoms = [f"symptom_{i}" for i in range(20)]  # Max allowed
        
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=large_symptoms,
            environmental_conditions={}
        )
        
        # Should not have errors for valid large list
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_very_long_symptom_string(self):
        """Test handling of very long symptom strings."""
        tool = DiagnoseDiseaseTool()
        
        # Create very long symptom string (but within limits)
        long_symptom = "a" * 100  # Max allowed length
        
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=[long_symptom],
            environmental_conditions={}
        )
        
        # Should not have errors for valid long string
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_unicode_symptom_handling(self):
        """Test handling of unicode characters in symptoms."""
        tool = DiagnoseDiseaseTool()
        
        unicode_symptoms = ["taches_jaunes", "pustules_jaunes", "symptôme_étrange"]
        
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=unicode_symptoms,
            environmental_conditions={}
        )
        
        # Should handle unicode without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        tool = DiagnoseDiseaseTool()
        
        errors = tool._validate_inputs(
            crop_type="",  # Empty string
            symptoms=[""],  # Empty string in list
            environmental_conditions={}
        )
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "error" for error in errors)
        assert any("symptoms[0]" in error.field and error.severity == "error" for error in errors)
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        tool = DiagnoseDiseaseTool()
        
        errors = tool._validate_inputs(
            crop_type=None,  # None value
            symptoms=None,  # None value
            environmental_conditions=None
        )
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "crop_type" and error.severity == "error" for error in errors)
        assert any(error.field == "symptoms" and error.severity == "error" for error in errors)
    
    def test_complex_environmental_conditions(self):
        """Test handling of complex environmental conditions."""
        tool = DiagnoseDiseaseTool()
        
        complex_conditions = {
            "humidity": 85.5,
            "temperature": 22.3,
            "rainfall": "frequent",
            "wind_speed": 15.2,
            "soil_moisture": 70.8
        }
        
        errors = tool._validate_inputs(
            crop_type="blé",
            symptoms=["taches_jaunes"],
            environmental_conditions=complex_conditions
        )
        
        # Should handle complex conditions without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
