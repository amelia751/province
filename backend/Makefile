# AI Legal OS Backend Makefile

.PHONY: help install install-dev test lint format type-check clean run deploy

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  type-check   Run type checking"
	@echo "  clean        Clean build artifacts"
	@echo "  run          Run development server"
	@echo "  dev          Run development server with monitoring"
	@echo "  server-start Start server using dev script"
	@echo "  server-stop  Stop server using dev script"
	@echo "  server-restart Restart server using dev script"
	@echo "  server-status Check server status"
	@echo "  server-logs  Show server logs"
	@echo "  deploy       Deploy infrastructure"

# Python environment
PYTHON := python3
PIP := pip3
VENV := venv
VENV_BIN := $(VENV)/bin

# Create virtual environment if it doesn't exist
$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip

# Install production dependencies
install: $(VENV)
	$(VENV_BIN)/pip install -r requirements.txt

# Install development dependencies
install-dev: $(VENV)
	$(VENV_BIN)/pip install -r requirements-dev.txt
	$(VENV_BIN)/pre-commit install

# Run tests
test: $(VENV)
	PYTHONPATH=src $(VENV_BIN)/pytest tests/ -v --cov=src/ai_legal_os --cov-report=html --cov-report=term

# Run linting
lint: $(VENV)
	PYTHONPATH=src $(VENV_BIN)/flake8 src/ tests/
	$(VENV_BIN)/black --check src/ tests/
	$(VENV_BIN)/isort --check-only src/ tests/

# Format code
format: $(VENV)
	$(VENV_BIN)/black src/ tests/
	$(VENV_BIN)/isort src/ tests/

# Run type checking
type-check: $(VENV)
	PYTHONPATH=src $(VENV_BIN)/mypy src/

# Clean build artifacts
clean:
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run development server
run: $(VENV)
	PYTHONPATH=src $(VENV_BIN)/uvicorn ai_legal_os.main:app --reload --host 0.0.0.0 --port 8000

# Deploy infrastructure
deploy: $(VENV)
	cd infrastructure && $(VENV_BIN)/cdk deploy --all --require-approval never

# Bootstrap CDK (run once per account/region)
bootstrap: $(VENV)
	cd infrastructure && $(VENV_BIN)/cdk bootstrap

# Synthesize CDK templates
synth: $(VENV)
	cd infrastructure && $(VENV_BIN)/cdk synth

# Destroy infrastructure (use with caution)
destroy: $(VENV)
	cd infrastructure && $(VENV_BIN)/cdk destroy --all

# Development server commands
dev:
	@echo "🔧 Starting development server with monitoring..."
	$(PYTHON) monitor-server.py

server-start:
	@echo "🚀 Starting server..."
	./dev-server.sh start

server-stop:
	@echo "🛑 Stopping server..."
	./dev-server.sh stop

server-restart:
	@echo "🔄 Restarting server..."
	./dev-server.sh restart

server-status:
	@echo "📊 Checking server status..."
	./dev-server.sh status

server-logs:
	@echo "📋 Showing server logs..."
	./dev-server.sh logs

server-clean:
	@echo "🧹 Cleaning server files..."
	./dev-server.sh clean