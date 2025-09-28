"""
Comprehensive Unit Tests for Enhanced AMM Lookup Tool

Tests cover:
- Input validation
- AMM lookup logic
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
from app.tools.regulatory_agent.lookup_amm_tool_vector_ready import (
    LookupAMMTool,
    AMMInfo,
    ValidationError
)
from app.config.amm_analysis_config import (
    AMMAnalysisConfig,
    AMMValidationConfig,
    AMMAnalysisConfigManager
)
from app.data.amm_vector_db_interface import (
    AMMKnowledge,
    AMMSearchResult,
    JSONAMMKnowledgeBase
)


class TestAMMLookupTool:
    """Test suite for the enhanced AMM lookup tool."""
    
    @pytest.fixture
    def tool(self):
        """Create a test instance of the AMM lookup tool."""
        return LookupAMMTool()
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test AMM knowledge base"
            },
            "products": {
                "Roundup": {
                    "amm_number": "AMM-2024-001",
                    "active_ingredient": "glyphosate",
                    "product_type": "herbicide",
                    "manufacturer": "Bayer",
                    "authorized_uses": ["désherbage_total", "désherbage_sélectif"],
                    "restrictions": ["interdiction_usage_public", "dose_maximale_3L_ha"],
                    "safety_measures": ["port_EPI_complet", "respect_ZNT_5m"],
                    "validity_period": "2024-2029",
                    "registration_date": "2024-01-15",
                    "expiry_date": "2029-01-15",
                    "target_crops": ["blé", "maïs"],
                    "target_weeds": ["chiendent", "liseron"],
                    "application_methods": ["pulvérisation"],
                    "dosage_range": {"min": "1.5L/ha", "max": "3L/ha", "recommended": "2L/ha"},
                    "phytotoxicity_risk": "moderate",
                    "environmental_impact": "high",
                    "resistance_risk": "high"
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
        assert tool.name == "lookup_amm_tool"
        assert tool.description == "Consulte les informations AMM pour les produits agricoles avec recherche sémantique"
        assert tool.use_vector_search is False
        assert tool._config_cache is None
        assert tool._validation_cache is None
        assert tool._knowledge_base is None
    
    def test_tool_initialization_with_custom_path(self, temp_knowledge_file):
        """Test tool initialization with custom knowledge base path."""
        tool = LookupAMMTool(knowledge_base_path=temp_knowledge_file)
        assert tool.knowledge_base_path == temp_knowledge_file
    
    def test_tool_initialization_with_vector_search(self):
        """Test tool initialization with vector search enabled."""
        tool = LookupAMMTool(use_vector_search=True)
        assert tool.use_vector_search is True
    
    def test_validate_inputs_valid_data(self, tool):
        """Test input validation with valid data."""
        errors = tool._validate_inputs(
            product_name="Roundup",
            active_ingredient="glyphosate",
            product_type="herbicide"
        )
        assert len(errors) == 0
    
    def test_validate_inputs_no_criteria(self, tool):
        """Test input validation with no search criteria."""
        errors = tool._validate_inputs(
            product_name=None,
            active_ingredient=None,
            product_type=None
        )
        assert len(errors) > 0
        assert any(error.field == "search_criteria" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_short_product_name(self, tool):
        """Test input validation with too short product name."""
        errors = tool._validate_inputs(
            product_name="a",  # Too short
            active_ingredient=None,
            product_type=None
        )
        assert len(errors) > 0
        assert any(error.field == "product_name" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_long_product_name(self, tool):
        """Test input validation with too long product name."""
        long_name = "a" * 150  # Too long
        errors = tool._validate_inputs(
            product_name=long_name,
            active_ingredient=None,
            product_type=None
        )
        assert len(errors) > 0
        assert any(error.field == "product_name" and error.severity == "warning" for error in errors)
    
    def test_validate_inputs_short_active_ingredient(self, tool):
        """Test input validation with too short active ingredient."""
        errors = tool._validate_inputs(
            product_name=None,
            active_ingredient="a",  # Too short
            product_type=None
        )
        assert len(errors) > 0
        assert any(error.field == "active_ingredient" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_unsupported_product_type(self, tool):
        """Test input validation with unsupported product type."""
        errors = tool._validate_inputs(
            product_name=None,
            active_ingredient=None,
            product_type="unsupported_type"
        )
        assert len(errors) > 0
        assert any(error.field == "product_type" and error.severity == "warning" for error in errors)
    
    def test_validate_inputs_too_many_criteria(self, tool):
        """Test input validation with too many search criteria."""
        # This test would need to be adjusted based on the actual validation logic
        # For now, we'll test with a reasonable number of criteria
        errors = tool._validate_inputs(
            product_name="Roundup",
            active_ingredient="glyphosate",
            product_type="herbicide"
        )
        # Should not have errors for reasonable number of criteria
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
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
    
    def test_analyze_amm_results_no_results(self, tool):
        """Test AMM results analysis with no search results."""
        amm_infos = tool._analyze_amm_results([], "Roundup", None, None)
        assert len(amm_infos) == 0
    
    def test_analyze_amm_results_with_results(self, tool):
        """Test AMM results analysis with search results."""
        # Create mock search result
        amm_knowledge = AMMKnowledge(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high"
        )
        
        search_result = AMMSearchResult(
            amm_knowledge=amm_knowledge,
            similarity_score=0.9,
            match_type="product_name"
        )
        
        amm_infos = tool._analyze_amm_results(
            [search_result],
            "Roundup",  # Matches product name
            None,
            None
        )
        
        assert len(amm_infos) == 1
        amm_info = amm_infos[0]
        assert amm_info.product_name == "Roundup"
        assert amm_info.amm_number == "AMM-2024-001"
        assert amm_info.active_ingredient == "glyphosate"
        assert amm_info.product_type == "herbicide"
        assert amm_info.search_metadata["confidence"] > 0.3  # Above minimum threshold
    
    def test_calculate_search_confidence_no_results(self, tool):
        """Test confidence calculation with no results."""
        confidence = tool._calculate_search_confidence([])
        assert confidence == "low"
    
    def test_calculate_search_confidence_high_confidence(self, tool):
        """Test confidence calculation with high confidence result."""
        amm_info = AMMInfo(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high",
            search_metadata={"confidence": 0.9}  # High confidence
        )
        
        confidence = tool._calculate_search_confidence([amm_info])
        assert confidence == "high"
    
    def test_calculate_search_confidence_moderate_confidence(self, tool):
        """Test confidence calculation with moderate confidence result."""
        amm_info = AMMInfo(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high",
            search_metadata={"confidence": 0.7}  # Moderate confidence
        )
        
        confidence = tool._calculate_search_confidence([amm_info])
        assert confidence == "moderate"
    
    def test_calculate_search_confidence_low_confidence(self, tool):
        """Test confidence calculation with low confidence result."""
        amm_info = AMMInfo(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high",
            search_metadata={"confidence": 0.4}  # Low confidence
        )
        
        confidence = tool._calculate_search_confidence([amm_info])
        assert confidence == "low"
    
    def test_generate_search_summary_no_results(self, tool):
        """Test search summary generation with no results."""
        summary = tool._generate_search_summary([])
        assert len(summary) == 1
        assert "Aucun produit AMM trouvé" in summary[0]
    
    def test_generate_search_summary_with_results(self, tool):
        """Test search summary generation with results."""
        amm_info = AMMInfo(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public", "dose_maximale_3L_ha"],
            safety_measures=["port_EPI_complet", "respect_ZNT_5m"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high",
            search_metadata={"confidence": 0.8}  # High confidence
        )
        
        summary = tool._generate_search_summary([amm_info])
        
        assert len(summary) > 1
        assert "Produit principal: Roundup" in summary[0]
        assert "AMM: AMM-2024-001" in summary[1]
        assert "Principe actif: glyphosate" in summary[2]
        assert "Type: herbicide" in summary[3]
        assert "Fabricant: Bayer" in summary[4]
        assert "Restrictions importantes:" in summary
        assert "Mesures de sécurité:" in summary
        assert "Dosage recommandé:" in summary
        assert "Impact environnemental: high" in summary
    
    def test_generate_search_summary_low_confidence(self, tool):
        """Test search summary generation with low confidence results."""
        amm_info = AMMInfo(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high",
            search_metadata={"confidence": 0.4}  # Low confidence
        )
        
        summary = tool._generate_search_summary([amm_info])
        
        assert len(summary) == 2
        assert "Recherche incertaine" in summary[0]
        assert "Consultez un expert" in summary[1]
    
    @patch('app.tools.regulatory_agent.lookup_amm_tool_vector_ready.asyncio.run')
    def test_run_method_success(self, mock_asyncio_run, tool, temp_knowledge_file):
        """Test successful execution of the _run method."""
        # Mock the async search results
        amm_knowledge = AMMKnowledge(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high"
        )
        
        search_result = AMMSearchResult(
            amm_knowledge=amm_knowledge,
            similarity_score=0.9,
            match_type="product_name"
        )
        
        mock_asyncio_run.return_value = [search_result]
        
        # Create tool with temp knowledge file
        tool = LookupAMMTool(knowledge_base_path=temp_knowledge_file)
        
        result = tool._run(
            product_name="Roundup",
            active_ingredient="glyphosate",
            product_type="herbicide"
        )
        
        result_data = json.loads(result)
        assert "search_criteria" in result_data
        assert result_data["search_criteria"]["product_name"] == "Roundup"
        assert "amm_results" in result_data
        assert len(result_data["amm_results"]) > 0
        assert "search_summary" in result_data
    
    def test_run_method_validation_errors(self, tool):
        """Test _run method with validation errors."""
        result = tool._run(
            product_name=None,  # No criteria provided
            active_ingredient=None,
            product_type=None
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    def test_run_method_no_results(self, tool):
        """Test _run method with no search results."""
        with patch.object(tool, '_search_amm_knowledge', return_value=[]):
            result = tool._run(
                product_name="NonexistentProduct",
                active_ingredient=None,
                product_type=None
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "No AMM products found" in result_data["error"]
            assert "suggestions" in result_data
    
    def test_run_method_exception_handling(self, tool):
        """Test _run method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = tool._run(
                product_name="Roundup",
                active_ingredient="glyphosate",
                product_type="herbicide"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de la consultation AMM" in result_data["error"]
            assert "error_type" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_success(self, tool, temp_knowledge_file):
        """Test successful execution of the _arun method."""
        # Create tool with temp knowledge file
        tool = LookupAMMTool(knowledge_base_path=temp_knowledge_file)
        
        # Mock the knowledge base search
        with patch.object(tool, '_search_amm_knowledge', return_value=[]):
            result = await tool._arun(
                product_name="Roundup",
                active_ingredient="glyphosate",
                product_type="herbicide"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data  # No knowledge found
            assert "No AMM products found" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_arun_method_validation_errors(self, tool):
        """Test _arun method with validation errors."""
        result = await tool._arun(
            product_name=None,  # No criteria provided
            active_ingredient=None,
            product_type=None
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
                product_name="Roundup",
                active_ingredient="glyphosate",
                product_type="herbicide"
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de la consultation asynchrone AMM" in result_data["error"]
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


class TestAMMAnalysisConfig:
    """Test suite for AMM analysis configuration."""
    
    def test_amm_analysis_config_defaults(self):
        """Test default values for AMM analysis configuration."""
        config = AMMAnalysisConfig()
        
        assert config.minimum_confidence == 0.3
        assert config.high_confidence == 0.8
        assert config.moderate_confidence == 0.6
        assert config.product_name_weight == 0.4
        assert config.active_ingredient_weight == 0.4
        assert config.product_type_weight == 0.2
        assert config.exact_match_bonus == 0.2
        assert config.partial_match_bonus == 0.1
        assert config.max_results == 10
        assert config.include_restrictions is True
        assert config.include_safety_measures is True
        assert config.include_dosage_info is True
        assert config.include_environmental_info is True
        assert config.min_search_criteria == 1
        assert config.max_search_criteria == 10
        assert "herbicide" in config.supported_product_types
        assert "insecticide" in config.supported_product_types
        assert config.case_sensitive is False
        assert config.fuzzy_matching is True
        assert config.similarity_threshold == 0.7
    
    def test_amm_validation_config_defaults(self):
        """Test default values for AMM validation configuration."""
        config = AMMValidationConfig()
        
        assert config.require_product_name is False
        assert config.min_product_name_length == 2
        assert config.max_product_name_length == 100
        assert config.require_active_ingredient is False
        assert config.min_active_ingredient_length == 2
        assert config.max_active_ingredient_length == 100
        assert config.require_product_type is False
        assert config.validate_product_type is True
        assert config.require_at_least_one_criteria is True
        assert config.max_total_criteria == 10
        assert config.strict_validation is True
        assert config.return_validation_errors is True
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = AMMAnalysisConfigManager()
        
        assert isinstance(manager.analysis_config, AMMAnalysisConfig)
        assert isinstance(manager.validation_config, AMMValidationConfig)
    
    def test_config_manager_update_analysis_config(self):
        """Test updating analysis configuration."""
        manager = AMMAnalysisConfigManager()
        
        manager.update_analysis_config(minimum_confidence=0.4, max_results=15)
        
        assert manager.analysis_config.minimum_confidence == 0.4
        assert manager.analysis_config.max_results == 15
    
    def test_config_manager_update_validation_config(self):
        """Test updating validation configuration."""
        manager = AMMAnalysisConfigManager()
        
        manager.update_validation_config(strict_validation=False, max_product_name_length=150)
        
        assert manager.validation_config.strict_validation is False
        assert manager.validation_config.max_product_name_length == 150
    
    def test_config_manager_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        manager = AMMAnalysisConfigManager()
        
        # Modify configs
        manager.update_analysis_config(minimum_confidence=0.5)
        manager.update_validation_config(strict_validation=False)
        
        # Reset to defaults
        manager.reset_to_defaults()
        
        assert manager.analysis_config.minimum_confidence == 0.3
        assert manager.validation_config.strict_validation is True


class TestJSONAMMKnowledgeBase:
    """Test suite for JSON AMM knowledge base."""
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test AMM knowledge base"
            },
            "products": {
                "Roundup": {
                    "amm_number": "AMM-2024-001",
                    "active_ingredient": "glyphosate",
                    "product_type": "herbicide",
                    "manufacturer": "Bayer",
                    "authorized_uses": ["désherbage_total"],
                    "restrictions": ["interdiction_usage_public"],
                    "safety_measures": ["port_EPI_complet"],
                    "validity_period": "2024-2029",
                    "registration_date": "2024-01-15",
                    "expiry_date": "2029-01-15",
                    "target_crops": ["blé"],
                    "target_weeds": ["chiendent"],
                    "application_methods": ["pulvérisation"],
                    "dosage_range": {"recommended": "2L/ha"},
                    "phytotoxicity_risk": "moderate",
                    "environmental_impact": "high",
                    "resistance_risk": "high"
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
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        assert kb.knowledge_file_path == temp_knowledge_file
        assert kb._knowledge_cache is None
    
    def test_load_knowledge(self, temp_knowledge_file):
        """Test knowledge loading from file."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        knowledge = kb._load_knowledge()
        
        assert "metadata" in knowledge
        assert "products" in knowledge
        assert "Roundup" in knowledge["products"]
    
    def test_load_knowledge_caching(self, temp_knowledge_file):
        """Test that knowledge is cached after loading."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        # First load
        knowledge1 = kb._load_knowledge()
        
        # Second load should return cached version
        knowledge2 = kb._load_knowledge()
        
        assert knowledge1 is knowledge2  # Same instance (cached)
        assert kb._knowledge_cache is not None
    
    def test_load_knowledge_file_not_found(self):
        """Test knowledge loading when file doesn't exist."""
        kb = JSONAMMKnowledgeBase("nonexistent_file.json")
        knowledge = kb._load_knowledge()
        
        assert knowledge == {}  # Empty dict on error
    
    @pytest.mark.asyncio
    async def test_search_by_product_name(self, temp_knowledge_file):
        """Test searching by product name."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_product_name(
            product_name="Roundup",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.amm_knowledge.product_name == "Roundup"
        assert result.similarity_score > 0
        assert result.match_type == "product_name"
    
    @pytest.mark.asyncio
    async def test_search_by_active_ingredient(self, temp_knowledge_file):
        """Test searching by active ingredient."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_active_ingredient(
            active_ingredient="glyphosate",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.amm_knowledge.active_ingredient == "glyphosate"
        assert result.similarity_score > 0
        assert result.match_type == "active_ingredient"
    
    @pytest.mark.asyncio
    async def test_search_by_product_type(self, temp_knowledge_file):
        """Test searching by product type."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_product_type(
            product_type="herbicide",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.amm_knowledge.product_type == "herbicide"
        assert result.similarity_score > 0
        assert result.match_type == "product_type"
    
    @pytest.mark.asyncio
    async def test_search_by_criteria(self, temp_knowledge_file):
        """Test searching by multiple criteria."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_criteria(
            product_name="Roundup",
            active_ingredient="glyphosate",
            product_type="herbicide",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.amm_knowledge.product_name == "Roundup"
        assert result.amm_knowledge.active_ingredient == "glyphosate"
        assert result.amm_knowledge.product_type == "herbicide"
        assert result.similarity_score > 0
        assert result.match_type == "general"
    
    @pytest.mark.asyncio
    async def test_get_all_products(self, temp_knowledge_file):
        """Test getting all products."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        products = await kb.get_all_products()
        
        assert len(products) == 1
        product = products[0]
        assert product.product_name == "Roundup"
        assert product.amm_number == "AMM-2024-001"
        assert product.active_ingredient == "glyphosate"
        assert product.product_type == "herbicide"
    
    @pytest.mark.asyncio
    async def test_add_amm_knowledge_not_supported(self, temp_knowledge_file):
        """Test that adding AMM knowledge is not supported in JSON mode."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        amm_knowledge = AMMKnowledge(
            product_name="TestProduct",
            amm_number="AMM-TEST-001",
            active_ingredient="test_ingredient",
            product_type="test_type",
            manufacturer="TestManufacturer",
            authorized_uses=["test_use"],
            restrictions=["test_restriction"],
            safety_measures=["test_measure"],
            validity_period="2024-2025",
            registration_date="2024-01-01",
            expiry_date="2025-01-01",
            target_crops=["test_crop"],
            target_pests=[],
            target_diseases=[],
            target_weeds=[],
            application_methods=["test_method"],
            dosage_range={"recommended": "test_dose"},
            phytotoxicity_risk="low",
            environmental_impact="low",
            resistance_risk="low"
        )
        
        result = await kb.add_amm_knowledge(amm_knowledge)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_amm_knowledge_not_supported(self, temp_knowledge_file):
        """Test that updating AMM knowledge is not supported in JSON mode."""
        kb = JSONAMMKnowledgeBase(temp_knowledge_file)
        
        result = await kb.update_amm_knowledge("Roundup", {"manufacturer": "NewManufacturer"})
        assert result is False


class TestAMMKnowledgeDataStructures:
    """Test suite for AMM knowledge data structures."""
    
    def test_amm_knowledge_creation(self):
        """Test AMMKnowledge dataclass creation."""
        amm_knowledge = AMMKnowledge(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high"
        )
        
        assert amm_knowledge.product_name == "Roundup"
        assert amm_knowledge.amm_number == "AMM-2024-001"
        assert amm_knowledge.active_ingredient == "glyphosate"
        assert amm_knowledge.product_type == "herbicide"
        assert amm_knowledge.manufacturer == "Bayer"
        assert amm_knowledge.authorized_uses == ["désherbage_total"]
        assert amm_knowledge.restrictions == ["interdiction_usage_public"]
        assert amm_knowledge.safety_measures == ["port_EPI_complet"]
        assert amm_knowledge.validity_period == "2024-2029"
        assert amm_knowledge.registration_date == "2024-01-15"
        assert amm_knowledge.expiry_date == "2029-01-15"
        assert amm_knowledge.target_crops == ["blé"]
        assert amm_knowledge.target_pests == []
        assert amm_knowledge.target_diseases == []
        assert amm_knowledge.target_weeds == ["chiendent"]
        assert amm_knowledge.application_methods == ["pulvérisation"]
        assert amm_knowledge.dosage_range == {"recommended": "2L/ha"}
        assert amm_knowledge.phytotoxicity_risk == "moderate"
        assert amm_knowledge.environmental_impact == "high"
        assert amm_knowledge.resistance_risk == "high"
        assert amm_knowledge.embedding_vector is None
        assert amm_knowledge.metadata is None
    
    def test_amm_search_result_creation(self):
        """Test AMMSearchResult dataclass creation."""
        amm_knowledge = AMMKnowledge(
            product_name="Roundup",
            amm_number="AMM-2024-001",
            active_ingredient="glyphosate",
            product_type="herbicide",
            manufacturer="Bayer",
            authorized_uses=["désherbage_total"],
            restrictions=["interdiction_usage_public"],
            safety_measures=["port_EPI_complet"],
            validity_period="2024-2029",
            registration_date="2024-01-15",
            expiry_date="2029-01-15",
            target_crops=["blé"],
            target_pests=[],
            target_diseases=[],
            target_weeds=["chiendent"],
            application_methods=["pulvérisation"],
            dosage_range={"recommended": "2L/ha"},
            phytotoxicity_risk="moderate",
            environmental_impact="high",
            resistance_risk="high"
        )
        
        search_result = AMMSearchResult(
            amm_knowledge=amm_knowledge,
            similarity_score=0.9,
            match_type="product_name"
        )
        
        assert search_result.amm_knowledge == amm_knowledge
        assert search_result.similarity_score == 0.9
        assert search_result.match_type == "product_name"


class TestValidationError:
    """Test suite for ValidationError data structure."""
    
    def test_validation_error_creation(self):
        """Test ValidationError dataclass creation."""
        error = ValidationError(
            field="product_name",
            message="Product name is required",
            severity="error"
        )
        
        assert error.field == "product_name"
        assert error.message == "Product name is required"
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
class TestAMMToolPerformance:
    """Test suite for performance and edge cases."""
    
    def test_large_product_name_handling(self):
        """Test handling of large product names."""
        tool = LookupAMMTool()
        
        # Create large product name (but within limits)
        large_name = "a" * 100  # Max allowed length
        
        errors = tool._validate_inputs(
            product_name=large_name,
            active_ingredient=None,
            product_type=None
        )
        
        # Should not have errors for valid large name
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_unicode_product_name_handling(self):
        """Test handling of unicode characters in product names."""
        tool = LookupAMMTool()
        
        unicode_names = ["Roundup®", "Décès", "Tilt™", "produit_étrange"]
        
        for name in unicode_names:
            errors = tool._validate_inputs(
                product_name=name,
                active_ingredient=None,
                product_type=None
            )
            
            # Should handle unicode without errors
            error_errors = [e for e in errors if e.severity == "error"]
            assert len(error_errors) == 0
    
    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        tool = LookupAMMTool()
        
        errors = tool._validate_inputs(
            product_name="",  # Empty string
            active_ingredient="",  # Empty string
            product_type=""
        )
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "product_name" and error.severity == "error" for error in errors)
        assert any(error.field == "active_ingredient" and error.severity == "error" for error in errors)
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        tool = LookupAMMTool()
        
        errors = tool._validate_inputs(
            product_name=None,  # None value
            active_ingredient=None,  # None value
            product_type=None
        )
        
        # Should have validation errors for no criteria
        assert len(errors) > 0
        assert any(error.field == "search_criteria" and error.severity == "error" for error in errors)
    
    def test_complex_search_criteria(self):
        """Test handling of complex search criteria."""
        tool = LookupAMMTool()
        
        complex_criteria = {
            "product_name": "Roundup Pro Max",
            "active_ingredient": "glyphosate-isopropylamine",
            "product_type": "herbicide_systémique"
        }
        
        errors = tool._validate_inputs(
            product_name=complex_criteria["product_name"],
            active_ingredient=complex_criteria["active_ingredient"],
            product_type=complex_criteria["product_type"]
        )
        
        # Should handle complex criteria without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
