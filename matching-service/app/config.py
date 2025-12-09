from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "SatispayFlow Matching Service"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Matching Configuration
    time_window_days: int = 90
    value_tolerance_percent: float = 10.0
    self_service_threshold: float = 500.0
    confidence_threshold: float = 70.0
    
    # Scoring Parameters
    temporal_decay_per_day: float = 1.0
    value_penalty_per_5_percent: float = 10.0
    unique_deal_bonus: float = 30.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
