# llm/llm_test.py
import os
import sys

# Add project root to path to allow absolute imports from 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# CORRECTED: Standardized import path to include 'src'
from src.llm.service import generate_commentary

# Sample context for testing
sample_context = {
    "symbol": "BTC",
    "timeframe": "15m",
    "signal": "LONG",
    "confidence": 78.2,
    "volatility": 2.3,
    "ema": "above price",
    "macd": "bullish crossover",
    "rsi": 63.4
}

backend = os.getenv("LLM_BACKEND", "llama")
print(f"🧪 Testing LLM backend: {backend.upper()}")

commentary = generate_commentary(sample_context)

print("\n--- Generated Commentary ---")
print(commentary)
print("--------------------------")