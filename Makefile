# Makefile
.DEFAULT_GOAL := help

# CORRECTED: Your Docker Hub username is set here
DOCKER_HUB_USERNAME := ballaj5
IMAGE_NAME := hodlbotv4.f
VERSION_TAG := $(shell date +%Y%m%d-%H%M%S)

help:
	@echo "💡 Available commands:"
	@echo "  make build           - Build the Docker image for the bot"
	@echo "  make run             - Start all services using Docker Compose (Bot + DB)"
	@echo "  make stop            - Stop all services started with Docker Compose"
	@echo "  make logs            - View logs from the running bot container"
	@echo "  make test            - Run all pytest tests inside the container"
	@echo "  make train           - Manually trigger the model training script"
	@echo "  make fetch-data      - Manually trigger historical data fetching"
	@echo "  make requirements    - Lock Python dependencies using pip-tools"
	@echo "  make push            - Build and push image to Docker Hub with version and latest tags"
	@echo "  make clean           - Remove temporary files and logs"

build:
	@echo "🐳 Building Docker image..."
	docker build -t $(DOCKER_HUB_USERNAME)/$(IMAGE_NAME):latest .
run:
	@echo "🚀 Starting all services (Bot + PostgreSQL)..."
	docker-compose up --build

stop:
	@echo "🛑 Stopping all services..."
	docker-compose down

logs:
	@echo "🔎 Tailing logs for the bot service..."
	docker-compose logs -f app

test:
	@echo "🧪 Running tests..."
	docker-compose run --rm app pytest tests/

train:
	@echo "🎯 Training model..."
	docker-compose run --rm app python -m scripts.train_model

fetch-data:
	@echo "📥 Fetching historical market data..."
	docker-compose run --rm app python -m src.data_fetch.fetch_futures_data

requirements:
	@echo "🔒 Locking dependencies with pip-tools..."
	docker-compose run --rm app pip-compile src/requirements.in -o src/requirements.txt

push: build
	@echo "🔐 Logging into Docker Hub..."
	@docker login -u $(DOKER_HUB_USERNAME)
	@echo "📦 Tagging image for release..."
	@docker tag $(DOCKER_HUB_USERNAME)/$(IMAGE_NAME):latest $(DOCKER_HUB_USERNAME)/$(IMAGE_NAME):$(VERSION_TAG)
	@echo "⬆️ Pushing image to Docker Hub..."
	@docker push $(DOCKER_HUB_USERNAME)/$(IMAGE_NAME):latest
	@docker push $(DOCKER_HUB_USERNAME)/$(IMAGE_NAME):$(VERSION_TAG)
	@echo "✅ Push complete."

clean:
	@echo "🧹 Cleaning up..."
	# CORRECTED: Removed 'sudo' to avoid permission issues
	rm -rf logs/*
	find . -type d -name "__pycache__" -exec rm -r {} +