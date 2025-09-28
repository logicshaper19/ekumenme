"""
Comprehensive Unit Tests for Enhanced Weather Data Tool

Tests cover:
- Input validation
- Weather data retrieval logic
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
from app.tools.weather_agent.get_weather_data_tool_vector_ready import (
    GetWeatherDataTool,
    WeatherCondition,
    ValidationError
)
from app.config.weather_data_config import (
    WeatherDataConfig,
    WeatherValidationConfig,
    WeatherDataConfigManager
)
from app.data.weather_vector_db_interface import (
    WeatherKnowledge,
    WeatherSearchResult,
    JSONWeatherKnowledgeBase
)


class TestWeatherDataTool:
    """Test suite for the enhanced weather data tool."""
    
    @pytest.fixture
    def tool(self):
        """Create a test instance of the weather data tool."""
        return GetWeatherDataTool()
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test weather knowledge base"
            },
            "weather_conditions": {
                "sunny": {
                    "condition_code": 1000,
                    "description": "Ensoleillé",
                    "agricultural_impact": "favorable",
                    "recommended_activities": ["traitements_phytosanitaires", "récolte"],
                    "restrictions": [],
                    "temperature_range": {"min": 15, "max": 35},
                    "humidity_range": {"min": 30, "max": 70},
                    "wind_range": {"min": 0, "max": 20}
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
        assert tool.name == "get_weather_data_tool"
        assert tool.description == "Récupère les données de prévision météorologique avec analyse agricole"
        assert tool.use_vector_search is False
        assert tool._config_cache is None
        assert tool._validation_cache is None
        assert tool._knowledge_base is None
    
    def test_validate_inputs_valid_data(self, tool):
        """Test input validation with valid data."""
        errors = tool._validate_inputs("Paris", 7)
        assert len(errors) == 0
    
    def test_validate_inputs_no_location(self, tool):
        """Test input validation with no location provided."""
        errors = tool._validate_inputs("", 7)
        assert len(errors) > 0
        assert any(error.field == "location" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_invalid_days(self, tool):
        """Test input validation with invalid days."""
        errors = tool._validate_inputs("Paris", 20)  # Too many days
        assert len(errors) > 0
        assert any(error.field == "days" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_short_location(self, tool):
        """Test input validation with location too short."""
        errors = tool._validate_inputs("P", 7)  # Too short
        assert len(errors) > 0
        assert any(error.field == "location" and error.severity == "error" for error in errors)
    
    def test_validate_inputs_long_location(self, tool):
        """Test input validation with location too long."""
        long_location = "A" * 150  # Too long
        errors = tool._validate_inputs(long_location, 7)
        assert len(errors) > 0
        assert any(error.field == "location" and error.severity == "warning" for error in errors)
    
    @pytest.mark.asyncio
    async def test_fetch_weather_data_success(self, tool):
        """Test successful weather data fetching."""
        mock_response_data = {
            "forecast": {
                "forecastday": [
                    {
                        "date": "2024-09-28",
                        "day": {
                            "mintemp_c": 10.0,
                            "maxtemp_c": 20.0,
                            "avghumidity": 70.0,
                            "maxwind_kph": 15.0,
                            "totalprecip_mm": 0.0,
                            "cloud": 30.0,
                            "uv": 5.0,
                            "condition": {
                                "code": 1000,
                                "text": "Sunny"
                            }
                        }
                    }
                ]
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await tool._fetch_weather_data("Paris", 1)
            
            assert "forecast" in result
            assert "forecastday" in result["forecast"]
            assert len(result["forecast"]["forecastday"]) == 1
    
    @pytest.mark.asyncio
    async def test_fetch_weather_data_api_error(self, tool):
        """Test weather data fetching with API error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await tool._fetch_weather_data("Paris", 1)
            
            assert "error" in result
            assert "WeatherAPI error 400" in result["error"]
    
    @pytest.mark.asyncio
    async def test_fetch_weather_data_timeout(self, tool):
        """Test weather data fetching with timeout."""
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError):
            result = await tool._fetch_weather_data("Paris", 1)
            
            assert "error" in result
            assert "WeatherAPI request timeout" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_weather_conditions(self, tool, temp_knowledge_file):
        """Test weather conditions analysis."""
        # Create tool with temp knowledge file
        tool = GetWeatherDataTool(knowledge_base_path=temp_knowledge_file)
        
        weather_data = {
            "forecast": {
                "forecastday": [
                    {
                        "date": "2024-09-28",
                        "day": {
                            "mintemp_c": 10.0,
                            "maxtemp_c": 20.0,
                            "avghumidity": 70.0,
                            "maxwind_kph": 15.0,
                            "totalprecip_mm": 0.0,
                            "cloud": 30.0,
                            "uv": 5.0,
                            "condition": {
                                "code": 1000,
                                "text": "Sunny"
                            }
                        }
                    }
                ]
            }
        }
        
        conditions = await tool._analyze_weather_conditions(weather_data)
        
        assert len(conditions) == 1
        condition = conditions[0]
        assert condition.date == "2024-09-28"
        assert condition.temperature_min == 10.0
        assert condition.temperature_max == 20.0
        assert condition.humidity == 70.0
        assert condition.condition_code == 1000
        assert condition.condition_description == "Sunny"
    
    @pytest.mark.asyncio
    async def test_get_agricultural_analysis(self, tool, temp_knowledge_file):
        """Test agricultural analysis retrieval."""
        # Create tool with temp knowledge file
        tool = GetWeatherDataTool(knowledge_base_path=temp_knowledge_file)
        
        day_info = {
            "mintemp_c": 15.0,
            "maxtemp_c": 25.0,
            "avghumidity": 60.0,
            "maxwind_kph": 10.0,
            "totalprecip_mm": 0.0,
            "cloud": 20.0,
            "uv": 6.0
        }
        
        analysis = await tool._get_agricultural_analysis(1000, "Sunny", day_info)
        
        assert "agricultural_impact" in analysis
        assert "recommended_activities" in analysis
        assert "restrictions" in analysis
        assert "confidence" in analysis
    
    def test_fallback_agricultural_analysis(self, tool):
        """Test fallback agricultural analysis."""
        day_info = {
            "avgtemp_c": 15.0,
            "avghumidity": 60.0,
            "maxwind_kph": 10.0,
            "totalprecip_mm": 0.0
        }
        
        analysis = tool._fallback_agricultural_analysis(day_info)
        
        assert "agricultural_impact" in analysis
        assert "recommended_activities" in analysis
        assert "restrictions" in analysis
        assert "confidence" in analysis
    
    def test_generate_agricultural_summary(self, tool):
        """Test agricultural summary generation."""
        weather_conditions = [
            WeatherCondition(
                date="2024-09-28",
                temperature_min=10.0,
                temperature_max=20.0,
                humidity=70.0,
                wind_speed=5.0,
                wind_direction="N",
                precipitation=0.0,
                cloud_cover=30.0,
                uv_index=5.0,
                condition_code=1000,
                condition_description="Sunny",
                agricultural_impact="favorable",
                recommended_activities=["traitements_phytosanitaires", "récolte"],
                restrictions=[]
            ),
            WeatherCondition(
                date="2024-09-29",
                temperature_min=5.0,
                temperature_max=15.0,
                humidity=90.0,
                wind_speed=10.0,
                wind_direction="S",
                precipitation=5.0,
                cloud_cover=80.0,
                uv_index=2.0,
                condition_code=1183,
                condition_description="Light Rain",
                agricultural_impact="défavorable",
                recommended_activities=["irrigation_naturelle"],
                restrictions=["éviter_traitements"]
            )
        ]
        
        summary = tool._generate_agricultural_summary(weather_conditions)
        
        assert summary["total_days"] == 2
        assert summary["favorable_days"] == 1
        assert summary["unfavorable_days"] == 1
        assert summary["treatment_opportunities"] == 1
        assert summary["harvest_opportunities"] == 1
        assert "éviter_traitements" in summary["weather_alerts"]
    
    @patch('app.tools.weather_agent.get_weather_data_tool_vector_ready.asyncio.run')
    def test_run_method_success(self, mock_asyncio_run, tool, temp_knowledge_file):
        """Test successful execution of the _run method."""
        # Mock the async weather data fetching
        mock_weather_data = {
            "forecast": {
                "forecastday": [
                    {
                        "date": "2024-09-28",
                        "day": {
                            "mintemp_c": 10.0,
                            "maxtemp_c": 20.0,
                            "avghumidity": 70.0,
                            "maxwind_kph": 15.0,
                            "totalprecip_mm": 0.0,
                            "cloud": 30.0,
                            "uv": 5.0,
                            "condition": {
                                "code": 1000,
                                "text": "Sunny"
                            }
                        }
                    }
                ]
            }
        }
        
        mock_asyncio_run.side_effect = [
            mock_weather_data,  # First call for _fetch_weather_data
            [WeatherCondition(
                date="2024-09-28",
                temperature_min=10.0,
                temperature_max=20.0,
                humidity=70.0,
                wind_speed=5.0,
                wind_direction="N",
                precipitation=0.0,
                cloud_cover=30.0,
                uv_index=5.0,
                condition_code=1000,
                condition_description="Sunny",
                agricultural_impact="favorable",
                recommended_activities=["traitements_phytosanitaires"],
                restrictions=[]
            )]  # Second call for _analyze_weather_conditions
        ]
        
        # Create tool with temp knowledge file
        tool = GetWeatherDataTool(knowledge_base_path=temp_knowledge_file)
        
        result = tool._run(location="Paris", days=1)
        
        result_data = json.loads(result)
        assert "location" in result_data
        assert "weather_conditions" in result_data
        assert "agricultural_summary" in result_data
        assert result_data["location"] == "Paris"
        assert result_data["forecast_period_days"] == 1
    
    def test_run_method_validation_errors(self, tool):
        """Test _run method with validation errors."""
        result = tool._run(location="", days=20)  # Invalid inputs
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    def test_run_method_api_error(self, tool):
        """Test _run method with API error."""
        with patch.object(tool, '_fetch_weather_data', return_value={"error": "API Error"}):
            result = tool._run(location="Paris", days=7)
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Failed to fetch weather data" in result_data["error"]
    
    def test_run_method_no_weather_data(self, tool):
        """Test _run method with no weather data."""
        with patch.object(tool, '_analyze_weather_conditions', return_value=[]):
            result = tool._run(location="Paris", days=7)
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "No weather data available" in result_data["error"]
    
    def test_run_method_exception_handling(self, tool):
        """Test _run method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = tool._run(location="Paris", days=7)
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de la récupération des données météo" in result_data["error"]
            assert "error_type" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_success(self, tool, temp_knowledge_file):
        """Test successful execution of the _arun method."""
        # Create tool with temp knowledge file
        tool = GetWeatherDataTool(knowledge_base_path=temp_knowledge_file)
        
        # Mock the weather data fetching
        with patch.object(tool, '_fetch_weather_data', return_value={"error": "API Error"}):
            result = await tool._arun(location="Paris", days=1)
            
            result_data = json.loads(result)
            assert "error" in result_data  # API error
            assert "Failed to fetch weather data" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_arun_method_validation_errors(self, tool):
        """Test _arun method with validation errors."""
        result = await tool._arun(location="", days=20)  # Invalid inputs
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Validation errors" in result_data["error"]
        assert "validation_errors" in result_data
    
    @pytest.mark.asyncio
    async def test_arun_method_exception_handling(self, tool):
        """Test _arun method exception handling."""
        with patch.object(tool, '_validate_inputs', side_effect=Exception("Test error")):
            result = await tool._arun(location="Paris", days=7)
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "Erreur lors de la récupération asynchrone des données météo" in result_data["error"]
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


class TestWeatherDataConfig:
    """Test suite for weather data configuration."""
    
    def test_weather_data_config_defaults(self):
        """Test default values for weather data configuration."""
        config = WeatherDataConfig()
        
        assert config.api_key == "b6683958ab174bb6ae0134111252809"
        assert config.base_url == "https://api.weatherapi.com/v1"
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.max_days == 14
        assert config.min_days == 1
        assert config.default_days == 7
        assert config.temperature_weight == 0.3
        assert config.humidity_weight == 0.2
        assert config.wind_weight == 0.2
        assert config.precipitation_weight == 0.3
        assert config.minimum_confidence == 0.7
        assert config.high_confidence == 0.9
        assert config.moderate_confidence == 0.8
        assert config.treatment_optimal_temp_min == 10.0
        assert config.treatment_optimal_temp_max == 25.0
        assert config.harvest_optimal_temp_min == 15.0
        assert config.harvest_optimal_temp_max == 30.0
        assert config.planting_optimal_temp_min == 10.0
        assert config.planting_optimal_temp_max == 25.0
        assert config.include_agricultural_analysis is True
        assert config.include_weather_alerts is True
        assert config.include_historical_data is False
        assert config.cache_duration_hours == 1
        assert config.require_location is True
        assert config.validate_days_range is True
        assert config.max_location_length == 100
        assert config.min_location_length == 2
        assert config.use_fallback_data is True
        assert config.log_api_errors is True
        assert config.return_detailed_errors is True
    
    def test_weather_validation_config_defaults(self):
        """Test default values for weather validation configuration."""
        config = WeatherValidationConfig()
        
        assert config.require_location is True
        assert config.min_location_length == 2
        assert config.max_location_length == 100
        assert config.validate_location_format is True
        assert config.require_days is False
        assert config.min_days == 1
        assert config.max_days == 14
        assert config.validate_days_range is True
        assert config.validate_api_key is True
        assert config.check_api_limits is True
        assert config.strict_validation is True
        assert config.return_validation_errors is True
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = WeatherDataConfigManager()
        
        assert isinstance(manager.weather_config, WeatherDataConfig)
        assert isinstance(manager.validation_config, WeatherValidationConfig)
    
    def test_config_manager_update_weather_config(self):
        """Test updating weather configuration."""
        manager = WeatherDataConfigManager()
        
        manager.update_weather_config(timeout_seconds=60, max_days=10)
        
        assert manager.weather_config.timeout_seconds == 60
        assert manager.weather_config.max_days == 10
    
    def test_config_manager_update_validation_config(self):
        """Test updating validation configuration."""
        manager = WeatherDataConfigManager()
        
        manager.update_validation_config(strict_validation=False, max_days=21)
        
        assert manager.validation_config.strict_validation is False
        assert manager.validation_config.max_days == 21
    
    def test_config_manager_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        manager = WeatherDataConfigManager()
        
        # Modify configs
        manager.update_weather_config(timeout_seconds=60)
        manager.update_validation_config(strict_validation=False)
        
        # Reset to defaults
        manager.reset_to_defaults()
        
        assert manager.weather_config.timeout_seconds == 30
        assert manager.validation_config.strict_validation is True


class TestJSONWeatherKnowledgeBase:
    """Test suite for JSON weather knowledge base."""
    
    @pytest.fixture
    def sample_knowledge_base(self):
        """Create a sample knowledge base for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "Test weather knowledge base"
            },
            "weather_conditions": {
                "sunny": {
                    "condition_code": 1000,
                    "description": "Ensoleillé",
                    "agricultural_impact": "favorable",
                    "recommended_activities": ["traitements_phytosanitaires", "récolte"],
                    "restrictions": [],
                    "temperature_range": {"min": 15, "max": 35},
                    "humidity_range": {"min": 30, "max": 70},
                    "wind_range": {"min": 0, "max": 20}
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
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        assert kb.knowledge_file_path == temp_knowledge_file
        assert kb._knowledge_cache is None
    
    def test_load_knowledge(self, temp_knowledge_file):
        """Test knowledge loading from file."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        knowledge = kb._load_knowledge()
        
        assert "metadata" in knowledge
        assert "weather_conditions" in knowledge
        assert "sunny" in knowledge["weather_conditions"]
    
    def test_load_knowledge_caching(self, temp_knowledge_file):
        """Test that knowledge is cached after loading."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        # First load
        knowledge1 = kb._load_knowledge()
        
        # Second load should return cached version
        knowledge2 = kb._load_knowledge()
        
        assert knowledge1 is knowledge2  # Same instance (cached)
        assert kb._knowledge_cache is not None
    
    def test_load_knowledge_file_not_found(self):
        """Test knowledge loading when file doesn't exist."""
        kb = JSONWeatherKnowledgeBase("nonexistent_file.json")
        knowledge = kb._load_knowledge()
        
        assert knowledge == {}  # Empty dict on error
    
    @pytest.mark.asyncio
    async def test_search_by_condition(self, temp_knowledge_file):
        """Test searching by condition."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_condition(
            condition_name="sunny",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.weather_knowledge.condition_name == "sunny"
        assert result.similarity_score > 0
        assert result.match_type == "condition"
    
    @pytest.mark.asyncio
    async def test_search_by_agricultural_impact(self, temp_knowledge_file):
        """Test searching by agricultural impact."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_agricultural_impact(
            impact="favorable",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.weather_knowledge.condition_name == "sunny"
        assert result.similarity_score > 0
        assert result.match_type == "impact"
    
    @pytest.mark.asyncio
    async def test_search_by_activity(self, temp_knowledge_file):
        """Test searching by activity."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_activity(
            activity="traitements_phytosanitaires",
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.weather_knowledge.condition_name == "sunny"
        assert result.similarity_score > 0
        assert result.match_type == "activity"
    
    @pytest.mark.asyncio
    async def test_search_by_weather_parameters(self, temp_knowledge_file):
        """Test searching by weather parameters."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        results = await kb.search_by_weather_parameters(
            temperature=20.0,
            humidity=50.0,
            wind_speed=10.0,
            precipitation=0.0,
            limit=10
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.weather_knowledge.condition_name == "sunny"
        assert result.similarity_score > 0
        assert result.match_type == "general"
    
    @pytest.mark.asyncio
    async def test_get_all_weather_conditions(self, temp_knowledge_file):
        """Test getting all weather conditions."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        conditions = await kb.get_all_weather_conditions()
        
        assert len(conditions) == 1
        condition = conditions[0]
        assert condition.condition_name == "sunny"
        assert condition.condition_code == 1000
        assert condition.description == "Ensoleillé"
        assert condition.agricultural_impact == "favorable"
    
    @pytest.mark.asyncio
    async def test_add_weather_knowledge_not_supported(self, temp_knowledge_file):
        """Test that adding weather knowledge is not supported in JSON mode."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        weather_knowledge = WeatherKnowledge(
            condition_name="TestCondition",
            condition_code=9999,
            description="Test Description",
            agricultural_impact="test",
            recommended_activities=[],
            restrictions=[],
            temperature_range={},
            humidity_range={},
            wind_range={}
        )
        
        result = await kb.add_weather_knowledge(weather_knowledge)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_weather_knowledge_not_supported(self, temp_knowledge_file):
        """Test that updating weather knowledge is not supported in JSON mode."""
        kb = JSONWeatherKnowledgeBase(temp_knowledge_file)
        
        result = await kb.update_weather_knowledge("sunny", {"description": "Updated"})
        assert result is False


class TestWeatherKnowledgeDataStructures:
    """Test suite for weather knowledge data structures."""
    
    def test_weather_knowledge_creation(self):
        """Test WeatherKnowledge dataclass creation."""
        weather_knowledge = WeatherKnowledge(
            condition_name="sunny",
            condition_code=1000,
            description="Ensoleillé",
            agricultural_impact="favorable",
            recommended_activities=["traitements_phytosanitaires", "récolte"],
            restrictions=[],
            temperature_range={"min": 15, "max": 35},
            humidity_range={"min": 30, "max": 70},
            wind_range={"min": 0, "max": 20}
        )
        
        assert weather_knowledge.condition_name == "sunny"
        assert weather_knowledge.condition_code == 1000
        assert weather_knowledge.description == "Ensoleillé"
        assert weather_knowledge.agricultural_impact == "favorable"
        assert weather_knowledge.recommended_activities == ["traitements_phytosanitaires", "récolte"]
        assert weather_knowledge.restrictions == []
        assert weather_knowledge.temperature_range == {"min": 15, "max": 35}
        assert weather_knowledge.humidity_range == {"min": 30, "max": 70}
        assert weather_knowledge.wind_range == {"min": 0, "max": 20}
        assert weather_knowledge.precipitation_range is None
        assert weather_knowledge.cloud_cover_range is None
        assert weather_knowledge.uv_index_range is None
        assert weather_knowledge.embedding_vector is None
        assert weather_knowledge.metadata is None
    
    def test_weather_search_result_creation(self):
        """Test WeatherSearchResult dataclass creation."""
        weather_knowledge = WeatherKnowledge(
            condition_name="sunny",
            condition_code=1000,
            description="Ensoleillé",
            agricultural_impact="favorable",
            recommended_activities=["traitements_phytosanitaires"],
            restrictions=[],
            temperature_range={"min": 15, "max": 35},
            humidity_range={"min": 30, "max": 70},
            wind_range={"min": 0, "max": 20}
        )
        
        search_result = WeatherSearchResult(
            weather_knowledge=weather_knowledge,
            similarity_score=0.9,
            match_type="condition"
        )
        
        assert search_result.weather_knowledge == weather_knowledge
        assert search_result.similarity_score == 0.9
        assert search_result.match_type == "condition"


class TestValidationError:
    """Test suite for ValidationError data structure."""
    
    def test_validation_error_creation(self):
        """Test ValidationError dataclass creation."""
        error = ValidationError(
            field="location",
            message="Location is required",
            severity="error"
        )
        
        assert error.field == "location"
        assert error.message == "Location is required"
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
class TestWeatherDataToolPerformance:
    """Test suite for performance and edge cases."""
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in inputs."""
        tool = GetWeatherDataTool()
        
        errors = tool._validate_inputs("París", 7)  # Unicode character
        
        # Should handle unicode without errors
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0
    
    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        tool = GetWeatherDataTool()
        
        errors = tool._validate_inputs("", 0)
        
        # Should have validation errors
        assert len(errors) > 0
        assert any(error.field == "location" and error.severity == "error" for error in errors)
        assert any(error.field == "days" and error.severity == "error" for error in errors)
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        tool = GetWeatherDataTool()
        
        errors = tool._validate_inputs(None, None)
        
        # Should have validation errors for location
        assert len(errors) > 0
        assert any(error.field == "location" and error.severity == "error" for error in errors)
    
    def test_extreme_values_handling(self):
        """Test handling of extreme values."""
        tool = GetWeatherDataTool()
        
        # Test with very long location name
        long_location = "A" * 200
        errors = tool._validate_inputs(long_location, 1)
        
        # Should have warning for location too long
        assert len(errors) > 0
        assert any(error.field == "location" and error.severity == "warning" for error in errors)
        
        # Test with negative days
        errors = tool._validate_inputs("Paris", -1)
        
        # Should have error for negative days
        assert len(errors) > 0
        assert any(error.field == "days" and error.severity == "error" for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
