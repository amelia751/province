# Makefile for Tax Rules Connector

.PHONY: install test lint clean package deploy

# Virtual environment
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Install dependencies
install: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

# Development dependencies
install-dev: install
	$(PIP) install pytest pytest-mock black flake8 mypy

# Run tests
test: install-dev
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -v

# Lint code
lint: install-dev
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m flake8 src/ tests/
	$(PYTHON) -m mypy src/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Package for Fivetran
package: clean
	mkdir -p dist/
	tar -czf dist/tax-rules-connector-v1.0.0.tar.gz \
		src/ \
		connector.yaml \
		requirements.txt \
		README.md \
		setup.py

# Test connector locally
test-connector: install
	PYTHONPATH=src $(PYTHON) -c "from tax_rules_connector.connector import TaxRulesConnector; c = TaxRulesConnector(); print('Connector initialized successfully')"

# Run a basic connection test
test-connection: install
	PYTHONPATH=src $(PYTHON) -c "from tax_rules_connector.http_client import IRSHttpClient; client = IRSHttpClient(); result = client.test_connection('https://www.irs.gov'); print(f'Connection test: {\"PASSED\" if result else \"FAILED\"}')"

# Show help
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Lint and format code"
	@echo "  clean        - Clean build artifacts"
	@echo "  package      - Package for Fivetran deployment"
	@echo "  test-connector - Test connector initialization"
	@echo "  test-connection - Test HTTP connection to IRS"
	@echo "  help         - Show this help message"
