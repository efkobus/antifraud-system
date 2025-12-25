"""
Anti-fraud system settings.
Settings can be overridden via environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    
    db_file: str = 'antifraud.db'
    
    max_transactions_per_2min: int = 3
    max_amount_per_24h: float = 1000.0
    max_transaction_amount: float = 1000000.0
    
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    api_title: str = 'Anti-Fraud API'
    api_version: str = '1.0.0'
    
    log_level: str = 'INFO'
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

settings = Settings()
