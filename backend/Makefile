.PHONY: install dev test lint clean build docker-build docker-up

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

test-e2e:
	pytest tests/e2e/ -v --tb=short

test-cov:
	pytest tests/ --cov=app --cov-report=term-missing

lint:
	ruff check app/
	ruff format --check app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov logs

build:
	docker build -t candidate-validation-backend .

docker-build:
	docker build -t candidate-validation-backend .

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
