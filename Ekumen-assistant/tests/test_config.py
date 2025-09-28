"""
Tests for configuration management
"""

import pytest
import os
from unittest.mock import patch
from app.core.config import Settings, get_settings, FRENCH_AGRICULTURAL_REGIONS, FRENCH_CROP_TYPES


class TestSettings:
    """Test configuration settings"""
    
    def test_default_settings(self):
        """Test default configuration values"""
        settings = Settings()
        
        assert settings.PROJECT_NAME == "Assistant Agricole IA"
        assert settings.VERSION == "1.0.0"
        assert settings.DEFAULT_LANGUAGE == "fr"
        assert settings.DEFAULT_REGION == "FR"
        assert settings.API_V1_STR == "/api/v1"
    
    def test_environment_variables(self):
        """Test environment variable loading"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'OPENAI_API_KEY': 'test-openai-key',
            'ELEVENLABS_API_KEY': 'test-elevenlabs-key'
        }):
            settings = Settings()
            
            assert settings.SECRET_KEY == 'test-secret-key'
            assert settings.DATABASE_URL == 'postgresql://test:test@localhost:5432/test_db'
            assert settings.OPENAI_API_KEY == 'test-openai-key'
            assert settings.ELEVENLABS_API_KEY == 'test-elevenlabs-key'
    
    def test_openai_models_config(self):
        """Test OpenAI models configuration"""
        settings = Settings()
        
        # Check that all agents have configuration
        expected_agents = [
            'regulatory_agent', 'weather_agent', 'crop_health_agent',
            'farm_data_agent', 'planning_agent', 'sustainability_agent'
        ]
        
        for agent in expected_agents:
            assert agent in settings.OPENAI_MODELS_CONFIG
            config = settings.OPENAI_MODELS_CONFIG[agent]
            
            # Check required fields
            assert 'model' in config
            assert 'temperature' in config
            assert 'max_tokens' in config
            assert 'top_p' in config
            
            # Check value ranges
            assert 0.0 <= config['temperature'] <= 1.0
            assert config['max_tokens'] > 0
            assert 0.0 <= config['top_p'] <= 1.0
    
    def test_agricultural_constants(self):
        """Test agricultural constants"""
        # Test French agricultural regions
        assert len(FRENCH_AGRICULTURAL_REGIONS) > 0
        assert "11" in FRENCH_AGRICULTURAL_REGIONS  # Île-de-France
        assert "75" in FRENCH_AGRICULTURAL_REGIONS  # Nouvelle-Aquitaine
        
        # Test French crop types
        assert len(FRENCH_CROP_TYPES) > 0
        assert "blé" in FRENCH_CROP_TYPES
        assert "maïs" in FRENCH_CROP_TYPES
        assert "colza" in FRENCH_CROP_TYPES
    
    def test_supported_languages(self):
        """Test supported languages configuration"""
        settings = Settings()
        
        assert "fr" in settings.SUPPORTED_LANGUAGES
        assert "en" in settings.SUPPORTED_LANGUAGES
        assert len(settings.SUPPORTED_LANGUAGES) == 2
    
    def test_supported_regions(self):
        """Test supported regions configuration"""
        settings = Settings()
        
        assert "FR" in settings.SUPPORTED_REGIONS
        assert "BE" in settings.SUPPORTED_REGIONS
        assert "CH" in settings.SUPPORTED_REGIONS
        assert len(settings.SUPPORTED_REGIONS) == 3
    
    def test_voice_configuration(self):
        """Test voice processing configuration"""
        settings = Settings()
        
        assert settings.WHISPER_MODEL == "base"
        assert settings.MAX_AUDIO_DURATION == 300  # 5 minutes
        assert settings.ELEVENLABS_VOICE_ID is not None
    
    def test_agent_configuration(self):
        """Test agent-specific configuration"""
        settings = Settings()
        
        assert settings.AGENT_TIMEOUT == 30
        assert settings.MAX_CONVERSATION_HISTORY == 50
        assert settings.AGENT_RETRY_ATTEMPTS == 3
    
    def test_journal_configuration(self):
        """Test voice journal configuration"""
        settings = Settings()
        
        assert settings.JOURNAL_AUTO_SAVE is True
        assert settings.JOURNAL_BACKUP_INTERVAL == 300
        assert settings.MAX_JOURNAL_ENTRIES_PER_DAY == 100
    
    def test_multi_organization_configuration(self):
        """Test multi-organization configuration"""
        settings = Settings()
        
        assert settings.ENABLE_MULTI_ORG is True
        assert settings.DEFAULT_ORG_TYPE == "farm"
        assert "farm" in settings.SUPPORTED_ORG_TYPES
        assert "cooperative" in settings.SUPPORTED_ORG_TYPES
        assert "input_company" in settings.SUPPORTED_ORG_TYPES
        assert "advisor" in settings.SUPPORTED_ORG_TYPES


class TestGetSettings:
    """Test settings getter function"""
    
    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance"""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
