from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Union

class Settings(BaseSettings):
    # Server API Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # DeepFace Configuration
    DEEPFACE_MODELS: list[str] = ["age", "gender", "emotion"]
    DEEPFACE_BACKEND: str = "opencv"  # or 'retinaface' if accuracy > speed
    CACHE_EXPIRATION_SEC: float = 1.0  # How often to run deepface per tracked face ID
    
    # Tracking Configuration
    MAX_DISAPPEARED_FRAMES: int = 30
    MAX_DISTANCE_THRESHOLD: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
