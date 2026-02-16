.PHONY: help install test lint type-check dead-code check format clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package in development mode with dev dependencies
	pip install -e ".[dev]"

test:  ## Run tests with pytest
	pytest tests/ -v

lint:  ## Run ruff linter
	ruff check sprocketship tests

type-check:  ## Run mypy type checker
	mypy sprocketship

dead-code:  ## Detect unused code with vulture
	vulture sprocketship --min-confidence 80

check: lint type-check dead-code test  ## Run all checks (lint, type-check, dead-code, tests)

format:  ## Format code with ruff
	ruff format sprocketship tests

clean:  ## Remove build artifacts and cache files
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
