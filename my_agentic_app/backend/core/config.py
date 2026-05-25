"""
Configuration module for the application.
Loads environment variables required for LINE API and database connections.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Application settings containing secret keys and credentials.
    """
    PROJECT_NAME: str = "AI Operation Management System"
    
    # LINE Bot Configuration
    LINE_CHANNEL_SECRET: str = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN: str = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

    # Queue Configuration (e.g., Redis URL if using Celery/ARQ)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # LLM API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    TYPHOON_API_KEY: str = os.getenv("TYPHOON_API_KEY", "")
    THAI_LLM_API_KEY: str = os.getenv("THAI_LLM_API_KEY", "")

settings = Settings()