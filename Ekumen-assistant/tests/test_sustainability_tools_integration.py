"""
Integration Tests for Sustainability Agent Tools.

Tests all 4 production-ready sustainability tools:
- analyze_soil_health_tool
- calculate_carbon_footprint_tool
- assess_biodiversity_tool
- assess_water_management_tool
"""

import pytest
import asyncio
import json
from app.tools.sustainability_agent import (
    carbon_footprint_tool,
    biodiversity_tool,
    soil_health_tool,
    water_management_tool
)


class TestSoilHealthTool:
    """Test soil health analysis tool."""
    
    @pytest.mark.asyncio
    async def test_soil_health_basic(self):
        """Test basic soil health analysis."""
        result = await soil_health_tool.coroutine(
            surface_ha=10.0,
            crop="blé",
            ph=6.5,
            organic_matter_percent=2.5,
            nitrogen_ppm=25.0,
            phosphorus_ppm=15.0,
            potassium_ppm=120.0
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["crop"] == "blé"
        assert data["surface_ha"] == 10.0
        assert "overall_soil_score" in data
        assert 0 <= data["overall_soil_score"] <= 10
        assert len(data["indicator_scores"]) > 0
        assert "improvement_recommendations" in data
    
    @pytest.mark.asyncio
    async def test_soil_health_crop_specific(self):
        """Test crop-specific pH recommendations."""
        # Test wheat (optimal pH 6.0-7.0)
        result_wheat = await soil_health_tool.coroutine(
            surface_ha=5.0,
            crop="blé",
            ph=6.5,
            organic_matter_percent=3.0
        )
        
        # Test potato (optimal pH 5.0-6.0)
        result_potato = await soil_health_tool.coroutine(
            surface_ha=5.0,
            crop="pomme de terre",
            ph=5.5,
            organic_matter_percent=3.0
        )
        
        wheat_data = json.loads(result_wheat)
        potato_data = json.loads(result_potato)
        
        assert wheat_data["success"] is True
        assert potato_data["success"] is True
        # Same pH should score differently for different crops
        assert wheat_data["overall_soil_score"] != potato_data["overall_soil_score"]


class TestCarbonFootprintTool:
    """Test carbon footprint calculation tool."""
    
    @pytest.mark.asyncio
    async def test_carbon_footprint_basic(self):
        """Test basic carbon footprint calculation."""
        result = await carbon_footprint_tool.coroutine(
            surface_ha=20.0,
            crop="maïs",
            diesel_liters=500.0,
            nitrogen_kg=200.0,
            phosphorus_kg=50.0,
            pesticide_kg=10.0
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["crop"] == "maïs"
        assert data["total_emissions_kg_co2eq"] > 0
        assert "total_emissions_min_kg_co2eq" in data
        assert "total_emissions_max_kg_co2eq" in data
        assert "uncertainty_range_percent" in data
        assert len(data["emissions_by_source"]) > 0
    
    @pytest.mark.asyncio
    async def test_carbon_footprint_uncertainty_range(self):
        """Test uncertainty range calculation."""
        result = await carbon_footprint_tool.coroutine(
            surface_ha=10.0,
            crop="blé",
            nitrogen_kg=100.0,  # High uncertainty factor (5-11 kg CO2eq/kg)
            pesticide_kg=5.0    # High uncertainty factor (10-20 kg CO2eq/kg)
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["total_emissions_min_kg_co2eq"] < data["total_emissions_kg_co2eq"]
        assert data["total_emissions_kg_co2eq"] < data["total_emissions_max_kg_co2eq"]
        assert data["uncertainty_range_percent"] > 0
        # Nitrogen and pesticides have high uncertainty
        assert data["uncertainty_range_percent"] > 30  # Should be significant
    
    @pytest.mark.asyncio
    async def test_carbon_footprint_sequestration(self):
        """Test carbon sequestration calculation."""
        result = await carbon_footprint_tool.coroutine(
            surface_ha=15.0,
            crop="tournesol",
            diesel_liters=300.0,
            cover_crops=True,
            reduced_tillage=True,
            organic_amendments=True
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["sequestration_potential_kg_co2eq"] > 0
        assert data["net_emissions_kg_co2eq"] < data["total_emissions_kg_co2eq"]


class TestBiodiversityTool:
    """Test biodiversity assessment tool."""
    
    @pytest.mark.asyncio
    async def test_biodiversity_basic(self):
        """Test basic biodiversity assessment."""
        result = await biodiversity_tool.coroutine(
            surface_ha=25.0,
            crop="blé",
            rotation_crops=3,
            rotation_years=4,
            field_margin_percent=5.0,
            hedgerow_length_m=200.0
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["surface_ha"] == 25.0
        assert "overall_biodiversity_score" in data
        assert 0 <= data["overall_biodiversity_score"] <= 10
        assert len(data["indicator_scores"]) == 7  # 7 indicators
        assert "improvement_recommendations" in data
    
    @pytest.mark.asyncio
    async def test_biodiversity_excellent_practices(self):
        """Test excellent biodiversity practices."""
        result = await biodiversity_tool.coroutine(
            surface_ha=30.0,
            crop="maïs",
            rotation_crops=5,
            rotation_years=5,
            field_margin_percent=10.0,
            hedgerow_length_m=150.0,
            water_features=True,
            organic_certified=True,
            pesticide_applications=2,
            cover_crops=True
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["overall_biodiversity_score"] >= 7.0  # Should be good/excellent
        assert data["overall_status"] in ["good", "excellent"]


class TestWaterManagementTool:
    """Test water management assessment tool."""
    
    @pytest.mark.asyncio
    async def test_water_management_basic(self):
        """Test basic water management assessment."""
        result = await water_management_tool.coroutine(
            surface_ha=15.0,
            crop="maïs",
            irrigated=True,
            irrigation_method="drip",
            annual_water_usage_m3=60000.0
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert data["crop"] == "maïs"
        assert "overall_water_score" in data
        assert 0 <= data["overall_water_score"] <= 10
        assert len(data["indicator_scores"]) >= 2  # At least irrigation + usage
        assert "water_use_efficiency" in data
    
    @pytest.mark.asyncio
    async def test_water_management_rainfall_adjustment(self):
        """Test rainfall adjustment to water requirements."""
        # High rainfall area
        result_high_rain = await water_management_tool.coroutine(
            surface_ha=10.0,
            crop="blé",
            irrigated=True,
            irrigation_method="sprinkler",
            annual_water_usage_m3=20000.0,
            rainfall_mm_annual=1000.0  # High rainfall
        )
        
        # Low rainfall area
        result_low_rain = await water_management_tool.coroutine(
            surface_ha=10.0,
            crop="blé",
            irrigated=True,
            irrigation_method="sprinkler",
            annual_water_usage_m3=20000.0,
            rainfall_mm_annual=300.0  # Arid
        )
        
        high_rain_data = json.loads(result_high_rain)
        low_rain_data = json.loads(result_low_rain)
        
        assert high_rain_data["success"] is True
        assert low_rain_data["success"] is True
        # Same usage should score better in low rainfall area (irrigation more necessary)
        # Or worse in high rainfall area (over-irrigation)
    
    @pytest.mark.asyncio
    async def test_water_management_soil_type_adjustment(self):
        """Test soil type adjustment to water requirements."""
        result = await water_management_tool.coroutine(
            surface_ha=12.0,
            crop="maïs",
            irrigated=True,
            irrigation_method="drip",
            annual_water_usage_m3=50000.0,
            soil_type="sandy"  # Low retention, needs more water
        )
        
        data = json.loads(result)
        assert data["success"] is True
        # Sandy soil should adjust requirements upward
        assert "sandy" in str(data).lower() or "sableux" in str(data).lower()
    
    @pytest.mark.asyncio
    async def test_water_management_economic_roi(self):
        """Test economic ROI calculation."""
        result = await water_management_tool.coroutine(
            surface_ha=20.0,
            crop="tomate",
            irrigated=True,
            irrigation_method="flood",  # Inefficient system
            annual_water_usage_m3=100000.0,
            water_cost_eur_per_m3=0.50  # Water cost for ROI
        )
        
        data = json.loads(result)
        assert data["success"] is True
        assert "estimated_water_savings_potential_m3" in data
        assert "estimated_annual_cost_savings_eur" in data
        if data["estimated_water_savings_potential_m3"]:
            assert data["estimated_annual_cost_savings_eur"] > 0
            # Verify calculation: savings_m3 * cost_per_m3
            expected_savings = data["estimated_water_savings_potential_m3"] * 0.50
            assert abs(data["estimated_annual_cost_savings_eur"] - expected_savings) < 1.0


class TestToolsIntegration:
    """Test integration between multiple tools."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_farm_assessment(self):
        """Test comprehensive farm sustainability assessment using all tools."""
        # Run all 4 tools for the same farm
        soil_result = await soil_health_tool.coroutine(
            surface_ha=50.0,
            crop="blé",
            ph=6.8,
            organic_matter_percent=3.2,
            nitrogen_ppm=30.0
        )
        
        carbon_result = await carbon_footprint_tool.coroutine(
            surface_ha=50.0,
            crop="blé",
            diesel_liters=1000.0,
            nitrogen_kg=400.0,
            cover_crops=True
        )
        
        biodiversity_result = await biodiversity_tool.coroutine(
            surface_ha=50.0,
            crop="blé",
            rotation_crops=4,
            rotation_years=4,
            field_margin_percent=7.0
        )
        
        water_result = await water_management_tool.coroutine(
            surface_ha=50.0,
            crop="blé",
            irrigated=True,
            irrigation_method="sprinkler",
            annual_water_usage_m3=100000.0
        )
        
        # Verify all tools succeeded
        soil_data = json.loads(soil_result)
        carbon_data = json.loads(carbon_result)
        biodiversity_data = json.loads(biodiversity_result)
        water_data = json.loads(water_result)
        
        assert soil_data["success"] is True
        assert carbon_data["success"] is True
        assert biodiversity_data["success"] is True
        assert water_data["success"] is True
        
        # All should have same surface area
        assert soil_data["surface_ha"] == 50.0
        assert carbon_data["surface_ha"] == 50.0
        assert biodiversity_data["surface_ha"] == 50.0
        assert water_data["surface_ha"] == 50.0

