# src/logger.py
import logging
import json
import sys
from .config import config

class JsonFormatter(logging.Formatter):
    """Formats log records as JSON strings."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name="CryptoBot"):
    """Sets up a logger with a JSON formatter."""
    logger = logging.getLogger(name)
    
    # Prevents adding handlers multiple times in case of reloads
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(config.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Instantiate the main logger for use by other modules
logger = setup_logger()