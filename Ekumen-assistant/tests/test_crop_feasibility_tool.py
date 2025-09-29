"""
Unit tests for CheckCropFeasibilityTool
"""

import pytest
import json
from app.tools.planning_agent.check_crop_feasibility_tool import CheckCropFeasibilityTool


class TestCheckCropFeasibilityTool:
    """Test suite for crop feasibility tool"""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance"""
        return CheckCropFeasibilityTool()
    
    def test_coffee_in_dourdan_not_feasible(self, tool):
        """Test that coffee is not feasible in Dourdan"""
        result_str = tool._run(crop="café", location="Dourdan", include_alternatives=True)
        result = json.loads(result_str)
        
        assert result["crop"] == "café"
        assert result["location"] == "Dourdan"
        assert result["is_feasible"] == False, "Coffee should not be feasible in Dourdan"
        assert result["feasibility_score"] < 7.0, "Feasibility score should be low"
        assert len(result["limiting_factors"]) > 0, "Should have limiting factors"
        assert "frost" in str(result["limiting_factors"]).lower() or "gel" in str(result["limiting_factors"]).lower()
        assert result["indoor_cultivation"] == True, "Should be possible indoors"
        assert len(result["alternatives"]) > 0, "Should have alternatives"
    
    def test_coffee_alternatives_include_temperate_crops(self, tool):
        """Test that coffee alternatives include temperate-adapted crops"""
        result_str = tool._run(crop="café", location="Dourdan", include_alternatives=True)
        result = json.loads(result_str)
        
        alternatives = result["alternatives"]
        assert len(alternatives) > 0
        
        # Check for expected alternatives
        alt_names = [a["name"] for a in alternatives]
        assert any(name in ["figuier", "amandier", "vigne", "noisetier", "kiwi"] for name in alt_names)
        
        # Check that alternatives have proper structure
        for alt in alternatives:
            assert "name" in alt
            assert "hardiness_zone" in alt
            assert "description" in alt
    
    def test_wheat_in_france_feasible(self, tool):
        """Test that wheat is feasible in France"""
        result_str = tool._run(crop="blé", location="Paris", include_alternatives=False)
        result = json.loads(result_str)
        
        assert result["crop"] == "blé"
        assert result["is_feasible"] == True, "Wheat should be feasible in Paris"
        assert result["feasibility_score"] >= 7.0, "Feasibility score should be high"
        assert len(result["limiting_factors"]) == 0, "Should have no limiting factors"
    
    def test_climate_data_included(self, tool):
        """Test that climate data is included in response"""
        result_str = tool._run(crop="café", location="Dourdan")
        result = json.loads(result_str)
        
        assert "climate_data" in result
        climate = result["climate_data"]
        assert "temp_min_annual" in climate
        assert "temp_max_annual" in climate
        assert "frost_days" in climate
        assert "growing_season_length" in climate
        assert "hardiness_zone" in climate
        
        # Dourdan should have frost days
        assert climate["frost_days"] > 0
    
    def test_crop_requirements_included(self, tool):
        """Test that crop requirements are included in response"""
        result_str = tool._run(crop="café", location="Dourdan")
        result = json.loads(result_str)
        
        assert "crop_requirements" in result
        requirements = result["crop_requirements"]
        assert "temp_min" in requirements
        assert "temp_max" in requirements
        assert "frost_tolerance" in requirements
        assert "climate_type" in requirements
        assert "hardiness_zone" in requirements
        
        # Coffee should not tolerate frost
        assert requirements["frost_tolerance"] == False
    
    def test_unknown_crop_returns_error(self, tool):
        """Test that unknown crop returns error message"""
        result_str = tool._run(crop="banane_spatiale", location="Paris")
        result = json.loads(result_str)
        
        assert "error" in result
        assert result["is_feasible"] is None
        assert "non reconnue" in result["message"].lower()
    
    def test_location_fallback_to_paris(self, tool):
        """Test that unknown location falls back to Paris climate"""
        result_str = tool._run(crop="café", location="VilleInconnue")
        result = json.loads(result_str)
        
        # Should still work with Paris climate as fallback
        assert result["is_feasible"] is not None
        assert "climate_data" in result
    
    def test_recommendations_provided(self, tool):
        """Test that recommendations are provided"""
        result_str = tool._run(crop="café", location="Dourdan")
        result = json.loads(result_str)
        
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        
        # Should mention greenhouse or indoor cultivation
        recommendations_text = " ".join(result["recommendations"]).lower()
        assert "serre" in recommendations_text or "intérieur" in recommendations_text or "pot" in recommendations_text
    
    def test_marseille_warmer_climate(self, tool):
        """Test that Marseille has warmer climate than Dourdan"""
        dourdan_result = json.loads(tool._run(crop="café", location="Dourdan"))
        marseille_result = json.loads(tool._run(crop="café", location="Marseille"))
        
        dourdan_climate = dourdan_result["climate_data"]
        marseille_climate = marseille_result["climate_data"]
        
        # Marseille should have fewer frost days
        assert marseille_climate["frost_days"] < dourdan_climate["frost_days"]
        
        # Marseille should have higher minimum temperature
        assert marseille_climate["temp_min_annual"] > dourdan_climate["temp_min_annual"]
    
    def test_feasibility_score_calculation(self, tool):
        """Test that feasibility score is calculated correctly"""
        # Coffee in cold climate should have low score
        cold_result = json.loads(tool._run(crop="café", location="Normandie"))
        assert cold_result["feasibility_score"] < 7.0
        
        # Wheat in temperate climate should have high score
        wheat_result = json.loads(tool._run(crop="blé", location="Paris"))
        assert wheat_result["feasibility_score"] >= 7.0
    
    def test_limiting_factors_specific(self, tool):
        """Test that limiting factors are specific and informative"""
        result_str = tool._run(crop="café", location="Dourdan")
        result = json.loads(result_str)
        
        limiting_factors = result["limiting_factors"]
        assert len(limiting_factors) > 0
        
        # Should mention specific issues
        factors_text = " ".join(limiting_factors).lower()
        assert any(word in factors_text for word in ["température", "gel", "saison"])
    
    def test_no_alternatives_when_not_requested(self, tool):
        """Test that alternatives are not included when not requested"""
        result_str = tool._run(crop="café", location="Dourdan", include_alternatives=False)
        result = json.loads(result_str)
        
        assert result["alternatives"] == []
    
    def test_json_output_valid(self, tool):
        """Test that output is valid JSON"""
        result_str = tool._run(crop="café", location="Dourdan")
        
        # Should not raise exception
        result = json.loads(result_str)
        
        # Should have expected keys
        expected_keys = ["crop", "location", "is_feasible", "feasibility_score", 
                        "limiting_factors", "climate_data", "crop_requirements", 
                        "alternatives", "indoor_cultivation", "recommendations"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

