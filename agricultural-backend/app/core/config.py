"""
Application configuration settings.
"""

from typing import List, Optional
from pydantic import BaseSettings, validator
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Agricultural Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Database
    database_url: str = "postgresql://agri_user:agri_password@localhost:5432/agri_db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "agri_db"
    database_user: str = "agri_user"
    database_password: str = "agri_password"
    
    # Security
    secret_key: str = "your-super-secret-key-minimum-32-characters-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # MesParcelles API
    mesparcelles_api_url: str = "https://api.mesparcelles.fr/v1"
    mesparcelles_api_key: Optional[str] = None
    
    # EPHY Data
    ephy_data_path: str = "/data/ephy"
    ephy_csv_encoding: str = "utf-8"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "/tmp/uploads"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    @validator("allowed_hosts", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
