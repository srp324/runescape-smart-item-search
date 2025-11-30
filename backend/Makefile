# Makefile for backend development tasks

.PHONY: help install install-test test test-cov test-verbose clean lint format type-check init-db run

help:
	@echo "Backend Development Commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-test  - Install test dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make clean         - Remove generated files and caches"
	@echo "  make lint          - Run linter (flake8)"
	@echo "  make format        - Format code (black + isort)"
	@echo "  make type-check    - Run type checker (mypy)"
	@echo "  make init-db       - Initialize database"
	@echo "  make run           - Run FastAPI server"

install:
	pip install -r requirements.txt

install-test:
	pip install -r requirements-test.txt

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-verbose:
	pytest -v

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-api:
	pytest -m api

clean:
	rm -rf __pycache__
	rm -rf **/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type f -name "*.pyc" -delete

lint:
	flake8 . --exclude=venv,env,.venv,__pycache__,.pytest_cache,htmlcov

format:
	black .
	isort .

type-check:
	mypy . --ignore-missing-imports

init-db:
	python init_database.py

run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uvicorn main:app --host 0.0.0.0 --port 8000

