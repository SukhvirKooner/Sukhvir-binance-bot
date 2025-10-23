"""Configuration loader for environment variables and constants."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the Binance bot."""
    
    # API Configuration
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")
    BINANCE_TESTNET_BASE_URL: str = os.getenv(
        "BINANCE_TESTNET_BASE_URL", 
        "https://testnet.binancefuture.com"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "bot.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 30
    
    # API Configuration
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    
    # Order Configuration
    DEFAULT_TIME_IN_FORCE: str = "GTC"
    MIN_QUANTITY: float = 0.000001
    
    # Validation
    SYMBOL_PATTERN: str = r"^[A-Z0-9]{6,12}$"
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate that required configuration is present."""
        if not cls.BINANCE_API_KEY:
            raise ValueError("BINANCE_API_KEY environment variable is required")
        if not cls.BINANCE_API_SECRET:
            raise ValueError("BINANCE_API_SECRET environment variable is required")
    
    @classmethod
    def get_api_credentials(cls) -> tuple[str, str]:
        """Get API credentials as a tuple."""
        return cls.BINANCE_API_KEY, cls.BINANCE_API_SECRET


# Global config instance
config = Config()
