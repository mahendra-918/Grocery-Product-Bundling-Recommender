"""
Configuration and runtime settings for the Grocery Recommender FastAPI backend.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


class Settings(BaseSettings):
    """Application settings with environment variable override support."""

    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "Grocery Product Bundling Recommender API"
    VERSION: str = "1.0.0"
    ARTIFACT_VERSION: str = "fpgrowth-v1.0.0"
    API_V1_STR: str = "/api/v1"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Artifact file locations
    RULES_PATH: Path = MODELS_DIR / "association_rules.pkl"
    PRODUCTS_PATH: Path = MODELS_DIR / "products.json"
    BUNDLES_PATH: Path = MODELS_DIR / "top_bundles.json"
    
    # Recommendation thresholds
    DEFAULT_MIN_CONFIDENCE: float = 0.20
    DEFAULT_MIN_LIFT: float = 1.15
    DEFAULT_TOP_K: int = 5
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8501",
        "*"
    ]


settings = Settings()
