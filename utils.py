"""
Utility functions for IOT WiFi management.
"""
import logging
import sys
from typing import Dict, Any


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup structured logging similar to the original bunyan logger."""
    
    # Create logger
    logger = logging.getLogger('iotwifi')
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create JSON-like formatter
    formatter = logging.Formatter(
        '{"time":"%(asctime)s","level":%(levelno)s,"name":"%(name)s","msg":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


def parse_key_value_output(output: str) -> Dict[str, str]:
    """Parse command output with key=value format into dictionary."""
    result = {}
    
    for line in output.strip().split('\n'):
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            result[key.strip()] = value.strip()
    
    return result


def get_env_or_default(env_key: str, default: str) -> str:
    """Get environment variable or return default value."""
    import os
    value = os.getenv(env_key)
    if value is None or len(value) == 0:
        os.environ[env_key] = default
        return default
    return value
