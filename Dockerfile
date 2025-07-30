# --- Stage 1: Builder ---
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    python3-dev \
    python3-pip \
    python3.10-venv \
    ninja-build \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
WORKDIR /workspace/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final Image ---
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV LLAMA_MODEL_PATH=/models/llama-model.gguf
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/workspace

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    libgomp1 \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to /workspace/
WORKDIR /workspace/

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY ./src ./src
COPY ./scripts ./scripts
COPY ./tests ./tests
COPY ./requirements.txt .

# Make start script executable
RUN chmod +x scripts/start.sh

# Expose ports
EXPOSE 8050
EXPOSE 8888

# Default command
CMD ["bash", "/workspace/scripts/start.sh"]