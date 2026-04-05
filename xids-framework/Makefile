.PHONY: help install install-dev test lint format clean build docker-build docker-run serve

help:
	@echo "X-IDS Framework - Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make install-dev   - Install dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters (flake8, mypy)"
	@echo "  make format        - Format code (black, isort)"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build Python package"
	@echo "  make serve         - Run API server"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test,docs]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=xids --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-performance:
	pytest tests/performance/ -v

lint:
	flake8 src/xids/ tests/
	mypy src/xids/ --ignore-missing-imports

format:
	black src/xids/ tests/
	isort src/xids/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

serve:
	uvicorn src.xids.api.app:app --reload --host 0.0.0.0 --port 8000

serve-prod:
	uvicorn src.xids.api.app:app --host 0.0.0.0 --port 8000 --workers 8

docker-build:
	docker build -f Dockerfile -t xids:latest .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/models:/app/models xids:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

train:
	python scripts/train.py

evaluate:
	python scripts/evaluate.py

docs:
	cd docs && make html

docs-serve:
	python -m http.server --directory docs/_build/html 8001
