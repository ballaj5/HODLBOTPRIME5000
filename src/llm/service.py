# src/llm/service.py
import os
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
LLM_BACKEND = os.getenv("LLM_BACKEND", "llama").lower()
LLM_COMMENTARY_ENABLED = os.getenv("LLM_COMMENTARY", "true").lower() in ("true", "1")

# --- Efficient Model Loading (Singleton Pattern) ---
_llama_model = None

def get_llama_model():
    """
    Loads the Llama model into memory once and reuses the object on subsequent calls.
    """
    global _llama_model
    if _llama_model is None:
        try:
            from llama_cpp import Llama
            model_path = os.getenv("LLAMA_MODEL_PATH", "/workspace/models/llama-model.gguf")
            if not os.path.exists(model_path):
                 raise FileNotFoundError(f"Llama model not found at {model_path}")

            logger.info(f"Loading Llama model from {model_path} into memory...")
            
            # CORRECTED: Read LLaMA parameters from environment variables
            _llama_model = Llama(
                model_path=model_path,
                n_ctx=int(os.getenv("LLAMA_CONTEXT_SIZE", 8192)),
                verbose=False,
                n_gpu_layers=-1 # Use all available GPU layers
            )
            logger.info("✅ Llama model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load Llama model: {e}", exc_info=True)
            _llama_model = e
    
    if isinstance(_llama_model, Exception):
        raise _llama_model

    return _llama_model

def _build_prompt(context: Dict[str, Any]) -> str:
    """Builds a standardized prompt from a context dictionary."""
    signal_confidence = context.get("confidence", 0)
    
    if signal_confidence >= 90:
        tone = "🚀 Strong Signal:"
    elif signal_confidence >= 80:
        tone = "✅ Confident Signal:"
    else:
        tone = "🔍 Cautious Insight:"

    prompt = f"""{tone}
You are a crypto trading assistant. Analyze the following signal:
- Coin: {context.get("symbol", "N/A")}
- Timeframe: {context.get("timeframe", "N/A")}
- Signal: {context.get("signal", "N/A")}
- Confidence: {signal_confidence:.2f}%
- Volatility: {context.get("volatility", "N/A")}%
- EMA: {context.get("ema", "N/A")}
- MACD: {context.get("macd", "N/A")}
- RSI: {context.get("rsi", "N/A")}

Respond in 2-3 clear sentences with your trade rationale.
"""
    return prompt.strip()

def _get_openai_response(prompt: str) -> str:
    """Handles API call to OpenAI."""
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=float(os.getenv("LLAMA_TEMPERATURE", 0.7)),
            timeout=15,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ OpenAI API call failed: {e}")
        return "⚠️ OpenAI commentary unavailable due to an error."

def _get_llama_response(prompt: str) -> str:
    """Handles local inference with the globally loaded Llama model."""
    try:
        llm = get_llama_model()
        # CORRECTED: Read LLaMA parameters from environment for generation
        output = llm(
            prompt,
            max_tokens=256,
            stop=["\n", "</s>"],
            temperature=float(os.getenv("LLAMA_TEMPERATURE", 0.7)),
            top_k=int(os.getenv("LLAMA_TOP_K", 40)),
            top_p=float(os.getenv("LLAMA_TOP_P", 0.95))
        )
        return output["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"❌ Llama inference failed: {e}")
        return "⚠️ Llama commentary unavailable due to an error."

def generate_commentary(context: Dict[str, Any]) -> str:
    """Master function to generate LLM commentary based on the configured backend."""
    if not LLM_COMMENTARY_ENABLED:
        return "ℹ️ LLM commentary is disabled."

    prompt = _build_prompt(context)
    
    if LLM_BACKEND == "openai":
        return _get_openai_response(prompt)
    elif LLM_BACKEND == "llama":
        return _get_llama_response(prompt)
    else:
        logger.error(f"❌ Invalid LLM_BACKEND configured: '{LLM_BACKEND}'")
        return f"⚠️ Commentary unavailable: Invalid backend '{LLM_BACKEND}'."