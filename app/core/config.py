import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./traffic_detector.db"
    
    # API Keys
    tomtom_api_key: Optional[str] = None
    here_api_key: Optional[str] = None
    inrix_api_key: Optional[str] = None
    zillow_api_key: Optional[str] = None
    realtor_api_key: Optional[str] = None
    redfin_api_key: Optional[str] = None
    census_api_key: Optional[str] = None
    bls_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    mapbox_api_key: Optional[str] = None
    openweather_api_key: Optional[str] = None
    weather_api_key: Optional[str] = None
    
    # Application Settings
    debug: bool = False
    default_analysis_radius: int = 5000
    traffic_data_retention_days: int = 365
    max_concurrent_requests: int = 10
    
    # Investment Analysis Settings
    min_investment_score: float = 0.3
    max_investment_score: float = 1.0
    default_roi_threshold: float = 0.08
    
    # Historical Data Collection
    historical_data_days: int = 365
    data_collection_interval_hours: int = 1
    
    # API Rate Limits
    tomtom_rate_limit: int = 60
    zillow_rate_limit: int = 30
    census_rate_limit: int = 100
    
    # Atlanta-specific Settings
    default_region: str = "atlanta"
    atlanta_center_lat: float = 33.7490
    atlanta_center_lng: float = -84.3880
    atlanta_analysis_radius: int = 50
    atlanta_property_types: str = "residential,commercial,mixed-use"
    
    # Machine Learning Settings
    ml_model_path: str = "app/ml/models/"
    prediction_confidence_threshold: float = 0.7
    
    # Dashboard Settings
    dashboard_refresh_interval: int = 300
    max_data_points: int = 10000
    
    # Logging Settings
    log_level: str = "INFO"
    log_file: str = "logs/traffic_detector.log"
    
    # Security Settings
    secret_key: str = "your_secret_key_here"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Validate required API keys
def validate_api_keys():
    """Validate that required API keys are set"""
    missing_keys = []
    
    if not settings.tomtom_api_key:
        missing_keys.append("TOMTOM_API_KEY")
    
    if missing_keys:
        print(f"Warning: Missing API keys: {', '.join(missing_keys)}")
        print("The app will use simulated traffic data instead.")
        print("For real traffic data, get a TomTom API key from: https://developer.tomtom.com/")
    
    return len(missing_keys) == 0 