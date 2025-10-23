"""Structured JSON logger for the Binance bot."""

import json
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path

from ..config import config


class StructuredLogger:
    """Structured JSON logger that outputs to JSON Lines format."""
    
    def __init__(self, name: str = "binance_bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create rotating file handler
        log_file = Path(config.LOG_FILE)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.LOG_MAX_SIZE,
            backupCount=config.LOG_BACKUP_COUNT
        )
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # Also add console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data to remove sensitive information."""
        sanitized = data.copy()
        
        # Remove or mask sensitive fields
        sensitive_fields = ['api_secret', 'apiKey', 'signature', 'BINANCE_API_SECRET']
        
        for field in sensitive_fields:
            if field in sanitized:
                if isinstance(sanitized[field], str):
                    sanitized[field] = "***REDACTED***"
                else:
                    sanitized[field] = "***REDACTED***"
        
        # Mask partial API key
        if 'api_key' in sanitized and isinstance(sanitized['api_key'], str):
            api_key = sanitized['api_key']
            if len(api_key) > 8:
                sanitized['api_key'] = api_key[:4] + "***" + api_key[-4:]
        
        return sanitized
    
    def _log(self, level: str, component: str, event: str, **kwargs):
        """Internal logging method."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "component": component,
            "event": event,
        }
        
        # Add additional fields
        for key, value in kwargs.items():
            if key in ['request', 'response'] and isinstance(value, dict):
                log_entry[key] = self._sanitize_data(value)
            else:
                log_entry[key] = value
        
        # Log as JSON
        self.logger.log(getattr(logging, level.upper()), json.dumps(log_entry))
    
    def info(self, component: str, event: str, **kwargs):
        """Log info level message."""
        self._log("INFO", component, event, **kwargs)
    
    def warning(self, component: str, event: str, **kwargs):
        """Log warning level message."""
        self._log("WARNING", component, event, **kwargs)
    
    def error(self, component: str, event: str, **kwargs):
        """Log error level message."""
        self._log("ERROR", component, event, **kwargs)
    
    def debug(self, component: str, event: str, **kwargs):
        """Log debug level message."""
        self._log("DEBUG", component, event, **kwargs)


# Global logger instance
logger = StructuredLogger()
