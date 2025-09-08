"""
Application configuration settings.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = "Japanese Railway Translation API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Model settings
    ner_model_name: str = "linhdzqua148/xlm-roberta-ner-japanese-railway"
    translation_model_name: str = "linhdzqua148/opus-mt-ja-en-railway-7"
    
    # Entity mapping
    entity_csv_path: str = "./train_entity.csv"
    
    # Device settings
    use_cuda: bool = True
    
    # API settings
    max_text_length: int = 1000
    request_timeout: int = 30
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
