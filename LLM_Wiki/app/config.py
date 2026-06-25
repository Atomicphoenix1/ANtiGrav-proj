import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Security
    SECURITY_TOKEN: str = "change_me_in_production"

    # Google AI Studio / Gemini API Settings
    GEMINI_API_KEY: Optional[str] = None

    # OpenRouter Settings (Alternative for Free Models)
    OPENROUTER_API_KEY: Optional[str] = None
    USE_OPENROUTER: bool = False
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash:free"

    # GitHub Settings
    GITHUB_TOKEN: str
    GITHUB_REPO: str  # Format: "owner/repo"
    GITHUB_BRANCH: str = "main"
    OBSIDIAN_SUBFOLDER: str = "fatwas"

    # Local Cache
    CACHE_DIR: str = ".cache"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
