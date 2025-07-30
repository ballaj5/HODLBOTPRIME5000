# src/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    """
    Central configuration class for the application.
    Reads settings from environment variables.
    """
    # --- Critical API and Database Credentials ---
    try:
        # LLM & APIs
        LLM_BACKEND = os.environ['LLM_BACKEND'].lower()
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        LLAMA_MODEL_PATH = os.environ['LLAMA_MODEL_PATH']
        
        # Bybit
        BYBIT_API_KEY = os.environ['BYBIT_API_KEY']
        BYBIT_API_SECRET = os.environ['BYBIT_API_SECRET']
        
        # Telegram
        TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
        TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

        # Database
        DB_HOST = os.environ['DB_HOST']
        DB_PORT = os.environ['DB_PORT']
        DB_NAME = os.environ['DB_NAME']
        DB_USER = os.environ['DB_USER']
        DB_PASS = os.environ['DB_PASS']

    except KeyError as e:
        raise RuntimeError(f"❌ Missing critical environment variable: {e}") from e

    # --- Feature Toggles ---
    LLM_COMMENTARY_ENABLED = os.getenv("LLM_COMMENTARY", "true").lower() in ("true", "1")
    ENABLE_REALTIME_FEATURES = os.getenv("ENABLE_REALTIME_FEATURES", "true").lower() in ("true", "1")
    ENABLE_TRADING_LOOP = os.getenv("ENABLE_TRADING_LOOP", "true").lower() in ("true", "1")
    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() in ("true", "1")
    
    # --- Trading Parameters ---
    SYMBOL = 'BTC/USDT'
    TIMEFRAME = '1h'
    TRADE_AMOUNT = 0.001 # Example amount in BTC

    # --- System Paths (CORRECTED) ---
    MODEL_PATH = "/workspace/models/model.pkl"
    BACKUP_MODEL_PATH = "/workspace/models/backup_model.pkl"
    ALERT_FLAG_PATH = "/workspace/data/alerts_on.flag"
    
    # --- Logging ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Instantiate config for global access
config = Config()