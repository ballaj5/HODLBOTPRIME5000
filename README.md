# 🚀 AI-Powered Crypto Futures Bot with LLaMA

This bot predicts crypto price action, analyzes market signals (RSI, EMA, MACD), and generates high-confidence Telegram alerts using OpenAI or a local LLaMA model.

---

## 🧠 LLM Features

- Dual backend: `LLM_BACKEND=openai` or `llama`
- Supports OpenAI API and local GPU inference via `llama-cpp-python`
- LLM Commentary + Confidence % in alerts
- Alerts ranked by coin weight and LLM confidence
- Triggers if confidence is **≥ 70%**

---

### 🐳 Docker (GPU)

First, build the Docker image:
```bash
docker build -t llama-crypto-bot .

docker run --rm \
  --gpus all \
  -p 8050:8050 \
  -v "$(pwd)/models:/models" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  --env-file .env \
  llama-crypto-bot