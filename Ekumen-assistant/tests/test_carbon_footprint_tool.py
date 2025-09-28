"""
Unit Tests for Enhanced Carbon Footprint Tool
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch

from app.tools.sustainability_agent.calculate_carbon_footprint_tool_vector_ready import (
    CalculateCarbonFootprintTool,
    CarbonFootprintComponent,
    ValidationError
)

class TestCarbonFootprintTool:
    """Test suite for the enhanced carbon footprint tool."""
    
    @pytest.fixture
    def tool(self):
        """Create a test instance of the carbon footprint tool."""
        return CalculateCarbonFootprintTool()
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {"version": "1.0.0"},
            "emission_factors": {
                "fertilizers": {
                    "azote": {"co2_per_kg": 4.2, "reduction_potential": 0.3}
                },
                "practices": {
                    "spraying": {"co2_per_ha": 12.5, "reduction_potential": 0.3}
                }
            },
            "default_usage_rates": {
                "fertilizer_kg_per_ha": 0.1
            },
            "reduction_strategies": {
                "fertilizer": ["Optimiser les doses"]
            }
        }
    
    @pytest.fixture
    def temp_knowledge_file(self, sample_knowledge_base):
        """Create a temporary knowledge base file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_knowledge_base, f, ensure_ascii=False)
            temp_file = f.name
        
        yield temp_file
        os.unlink(temp_file)
    
    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool.name == "calculate_carbon_footprint_tool"
        assert tool._config_cache is None
    
    def test_validate_inputs_valid_data(self, tool):
        """Test input validation with valid data."""
        errors = tool._validate_inputs("spraying", ["azote"], 1.0, 1)
        assert len(errors) == 0
    
    def test_validate_inputs_no_practice_type(self, tool):
        """Test input validation with no practice type."""
        errors = tool._validate_inputs("", ["azote"], 1.0, 1)
        assert len(errors) > 0
        assert any(error.field == "practice_type" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_invalid_area(self, tool):
        """Test input validation with invalid area."""
        errors = tool._validate_inputs("spraying", ["azote"], 0.05, 1)  # Too small
        assert len(errors) > 0
        assert any(error.field == "area_ha" and error.severity == "error" for error in errors)
    
    def test_load_knowledge_base(self, tool, temp_knowledge_file):
        """Test knowledge base loading."""
        tool.knowledge_base_path = temp_knowledge_file
        knowledge = tool._load_knowledge_base()
        
        assert "metadata" in knowledge
        assert "emission_factors" in knowledge
        assert "azote" in knowledge["emission_factors"]["fertilizers"]
    
    def test_calculate_carbon_components(self, tool, temp_knowledge_file):
        """Test carbon components calculation."""
        tool.knowledge_base_path = temp_knowledge_file
        knowledge = tool._load_knowledge_base()
        
        components = tool._calculate_carbon_components(
            "spraying", ["azote"], 1.0, 1, knowledge
        )
        
        assert len(components) == 2  # practice + fertilizer
        assert any(c.component_type == "practice" for c in components)
        assert any(c.component_type == "fertilizer" for c in components)
    
    def test_generate_reduction_recommendations(self, tool, temp_knowledge_file):
        """Test reduction recommendations generation."""
        tool.knowledge_base_path = temp_knowledge_file
        knowledge = tool._load_knowledge_base()
        
        components = [
            CarbonFootprintComponent(
                component_type="fertilizer",
                emission_source="azote",
                co2_equivalent=15.0,
                percentage=50.0,
                reduction_potential=0.3
            )
        ]
        
        recommendations = tool._generate_reduction_recommendations(components, knowledge)
        
        assert len(recommendations) > 0
        assert any("Optimiser les doses" in rec for rec in recommendations)
    
    def test_run_method_success(self, tool, temp_knowledge_file):
        """Test successful execution of the _run method."""
        tool.knowledge_base_path = temp_knowledge_file
        
        result = tool._run(
            practice_type="spraying",
            inputs_used=["azote"],
            area_ha=1.0,
            duration_days=1
        )
        
        result_data = json.loads(result)
        assert "practice_type" in result_data
        assert "carbon_components" in result_data
        assert "total_carbon_footprint" in result_data
        assert result_data["practice_type"] == "spraying"
    
    def test_run_method_validation_errors(self, tool):
        """Test _run method with validation errors."""
        result = tool._run(
            practice_type="",  # Invalid
            inputs_used=[],
            area_ha=0.05,  # Too small
            duration_days=1
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
    
    def test_run_method_exception_handling(self, tool):
        """Test _run method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = tool._run(
                practice_type="spraying",
                inputs_used=["azote"],
                area_ha=1.0,
                duration_days=1
            )
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors du calcul de l'empreinte carbone" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_arun_method(self, tool, temp_knowledge_file):
        """Test asynchronous execution."""
        tool.knowledge_base_path = temp_knowledge_file
        
        result = await tool._arun(
            practice_type="spraying",
            inputs_used=["azote"],
            area_ha=1.0,
            duration_days=1
        )
        
        result_data = json.loads(result)
        assert "practice_type" in result_data
        assert result_data["practice_type"] == "spraying"
    
    def test_clear_cache(self, tool):
        """Test cache clearing functionality."""
        # Access config to populate cache
        tool._get_config()
        
        # Verify cache is populated
        assert tool._config_cache is not None
        
        # Clear cache
        tool.clear_cache()
        
        # Verify cache is cleared
        assert tool._config_cache is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
