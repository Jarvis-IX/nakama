"""
Application Configuration for Jarvis AI Assistant
Central configuration management
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """
    Main application configuration class.
    Loads settings from environment variables and provides sensible defaults.
    Includes fail-fast validation for critical settings.
    """

    # --- Core Application Settings ---
    APP_NAME: str = os.getenv('APP_NAME', 'Jarvis AI Assistant')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    MAX_CONVERSATION_HISTORY: int = int(os.getenv('MAX_CONVERSATION_HISTORY', '10'))

    # --- Supabase Database Configuration ---
    SUPABASE_URL: str = os.getenv('SUPABASE_URL')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY')

    # --- Ollama LLM Configuration ---
    OLLAMA_HOST: str = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
    DEFAULT_TEMPERATURE: float = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
    DEFAULT_MAX_TOKENS: int = int(os.getenv('DEFAULT_MAX_TOKENS', '1500'))

    # --- RAG and Vector Search Settings ---
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    SIMILARITY_THRESHOLD: float = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))
    MAX_SEARCH_RESULTS: int = int(os.getenv('MAX_SEARCH_RESULTS', '5'))
    DEFAULT_CHUNK_SIZE: int = int(os.getenv('DEFAULT_CHUNK_SIZE', '512'))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv('DEFAULT_CHUNK_OVERLAP', '50'))

    # --- File Storage Settings ---
    TEMP_STORAGE_PATH: str = os.getenv('TEMP_STORAGE_PATH', './temp-storage')

    # --- API Performance Settings ---
    API_CACHE_TTL: int = int(os.getenv('API_CACHE_TTL', '300'))

    @classmethod
    def validate_config(cls) -> None:
        """
        Validates critical configuration settings.
        Raises ValueError if a required setting is missing or invalid.
        """
        issues = []
        if not cls.SUPABASE_URL or 'your_supabase_url' in cls.SUPABASE_URL:
            issues.append("SUPABASE_URL is not set or is a placeholder.")
        
        if not cls.SUPABASE_KEY or 'your_supabase_anon_key' in cls.SUPABASE_KEY:
            issues.append("SUPABASE_KEY is not set or is a placeholder.")

        if not (0.0 <= cls.SIMILARITY_THRESHOLD <= 1.0):
            issues.append(f"SIMILARITY_THRESHOLD must be between 0 and 1, but is {cls.SIMILARITY_THRESHOLD}")

        if cls.MAX_SEARCH_RESULTS < 1:
            issues.append(f"MAX_SEARCH_RESULTS must be at least 1, but is {cls.MAX_SEARCH_RESULTS}")

        if issues:
            error_message = "Critical configuration errors found: " + ", ".join(issues)
            logger.error(error_message)
            raise ValueError(error_message)

    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Returns a dictionary of LLM-specific settings."""
        return {
            "model_name": cls.OLLAMA_MODEL,
            "host": cls.OLLAMA_HOST,
            "temperature": cls.DEFAULT_TEMPERATURE,
            "max_tokens": cls.DEFAULT_MAX_TOKENS
        }

    @classmethod
    def get_embedding_config(cls) -> Dict[str, Any]:
        """Returns a dictionary of embedding-specific settings."""
        return {
            "model_name": cls.EMBEDDING_MODEL,
            "chunk_size": cls.DEFAULT_CHUNK_SIZE,
            "chunk_overlap": cls.DEFAULT_CHUNK_OVERLAP
        }

    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Returns a dictionary of database-specific settings."""
        return {
            "url": cls.SUPABASE_URL,
            "key": cls.SUPABASE_KEY,
            "similarity_threshold": cls.SIMILARITY_THRESHOLD,
            "max_results": cls.MAX_SEARCH_RESULTS
        }

# --- Run validation on import ---
try:
    AppConfig.validate_config()
except ValueError as e:
    logger.critical(f"Application startup failed due to configuration error: {e}")
    # In a real application, you might exit here, e.g., sys.exit(1)

