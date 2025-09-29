"""
Agricultural Chatbot Configuration
Centralized configuration management for the agricultural chatbot system
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with agricultural chatbot specific configurations"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ekumen Assistant"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Intelligent Agricultural Assistant with Voice Interface"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Configuration - Connect to main Ekumenbackend database (agri_db)
    # This database contains both MesParcelles data and EPHY regulatory data
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://agri_user:agri_password@localhost:5432/agri_db"
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://agri_user:agri_password@localhost:5432/agri_db"
    )
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ORGANIZATION: Optional[str] = os.getenv("OPENAI_ORGANIZATION")
    OPENAI_DEFAULT_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_FALLBACK_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_REQUEST_TIMEOUT: int = 60
    OPENAI_MAX_RETRIES: int = 3
    
    # Model-specific settings for different agents
    OPENAI_MODELS_CONFIG: Dict[str, Dict[str, Any]] = {
        "regulatory_agent": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.0,
            "max_tokens": 2500,
            "top_p": 1.0
        },
        "weather_agent": {
            "model": "gpt-4-turbo-preview", 
            "temperature": 0.2,
            "max_tokens": 2000,
            "top_p": 0.9
        },
        "crop_health_agent": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.3,
            "max_tokens": 2500,
            "top_p": 0.9
        },
        "farm_data_agent": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.1,
            "max_tokens": 2000,
            "top_p": 1.0
        },
        "planning_agent": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.4,
            "max_tokens": 3000,
            "top_p": 0.8
        },
        "sustainability_agent": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.3,
            "max_tokens": 2500,
            "top_p": 0.9
        }
    }
    
    # Voice Processing Configuration
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam voice
    WHISPER_MODEL: str = "base"
    MAX_AUDIO_DURATION: int = 300  # 5 minutes max
    
    # Agricultural API Configuration
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_BASE_URL: str = "http://api.weatherapi.com/v1"
    METEO_FRANCE_API_KEY: str = os.getenv("METEO_FRANCE_API_KEY", "")
    
    # Regulatory API Configuration
    E_PHY_API_URL: str = "https://ephy.anses.fr/ws/rest"
    AMM_API_URL: str = "https://ephy.anses.fr/ws/rest/amm"
    
    # Farm Data API Configuration
    MES_PARCELLES_API_URL: str = os.getenv("MES_PARCELLES_API_URL", "")
    MES_PARCELLES_API_KEY: str = os.getenv("MES_PARCELLES_API_KEY", "")
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8080",
        "https://agricultural-chatbot.com",
        "https://www.agricultural-chatbot.com",
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_PREFIX: str = "agricultural_chatbot:"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"]
    UPLOAD_DIR: str = "uploads"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    ENABLE_METRICS: bool = True
    
    # Agricultural Specific Settings
    DEFAULT_LANGUAGE: str = "fr"
    SUPPORTED_LANGUAGES: List[str] = ["fr", "en"]
    DEFAULT_REGION: str = "FR"
    SUPPORTED_REGIONS: List[str] = ["FR", "BE", "CH"]
    
    # Agent Configuration
    AGENT_TIMEOUT: int = 30  # seconds
    MAX_CONVERSATION_HISTORY: int = 50
    AGENT_RETRY_ATTEMPTS: int = 3
    
    # Voice Journal Configuration
    JOURNAL_AUTO_SAVE: bool = True
    JOURNAL_BACKUP_INTERVAL: int = 300  # 5 minutes
    MAX_JOURNAL_ENTRIES_PER_DAY: int = 100
    
    # Multi-organization Configuration
    ENABLE_MULTI_ORG: bool = True
    DEFAULT_ORG_TYPE: str = "farm"
    SUPPORTED_ORG_TYPES: List[str] = ["farm", "cooperative", "input_company", "advisor"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __post_init__(self):
        """Validate critical settings after initialization"""
        if not self.SECRET_KEY or self.SECRET_KEY == "your_secret_key_here_generate_a_strong_random_string":
            raise ValueError("SECRET_KEY environment variable is required and must be set to a secure value")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


# Agricultural region codes for French agriculture
FRENCH_AGRICULTURAL_REGIONS = {
    "11": "Île-de-France",
    "24": "Centre-Val de Loire", 
    "27": "Bourgogne-Franche-Comté",
    "28": "Normandie",
    "32": "Hauts-de-France",
    "44": "Grand Est",
    "52": "Pays de la Loire",
    "53": "Bretagne",
    "75": "Nouvelle-Aquitaine",
    "76": "Occitanie",
    "84": "Auvergne-Rhône-Alpes",
    "93": "Provence-Alpes-Côte d'Azur",
    "94": "Corse"
}

# Crop types for French agriculture
FRENCH_CROP_TYPES = [
    "blé", "orge", "maïs", "colza", "tournesol", "soja", "pomme de terre",
    "betterave", "légumes", "fruits", "vigne", "prairies", "forêt"
]

# Agricultural seasons
AGRICULTURAL_SEASONS = {
    "spring": "Printemps",
    "summer": "Été", 
    "autumn": "Automne",
    "winter": "Hiver"
}
