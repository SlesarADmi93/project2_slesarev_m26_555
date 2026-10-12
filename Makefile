.PHONY: help install run test lint lint-fix clean build check-publish

GREEN := \033[0;32m
NC := \033[0m # No Color

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies (uv sync)"
	@echo "  make build            - Build the package (uv build)"
	@echo "  make run              - Run the application (uv run database)"
	@echo "  make lint             - Check code style with Ruff"
	@echo "  make lint-fix         - Auto-fix code style issues with Ruff"
	@echo "  make check-publish    - Check package metadata before publishing"
	@echo "  make clean            - Clean temporary files, data, and metadata"

install:
	@echo "$(GREEN)Installing dependencies via uv...$(NC)"
	uv sync

build:
	@echo "$(GREEN)Building package...$(NC)"
	uv build

run:
	@echo "$(GREEN)Starting database...$(NC)"
	uv run database

lint:
	@echo "$(GREEN)Checking code style (Ruff)...$(NC)"
	uv run ruff check .

lint-fix:
	@echo "$(GREEN)Fixing code style (Ruff)...$(NC)"
	uv run ruff check . --fix

check-publish:
	@echo "$(GREEN)Checking package metadata...$(NC)"
	uv build
	uvx twine check dist/*

clean:
	@echo "$(GREEN)Cleaning temporary files, data, and metadata...$(NC)"
	python -c "import shutil, os; [shutil.rmtree(p) for p in ['__pycache__', '.pytest_cache', 'dist', 'data'] if os.path.exists(p)]; [os.remove(f) for f in ['db_meta.json'] + [f for f in os.listdir('.') if f.endswith('.egg-info')] if os.path.exists(f)]"
	uv cache clean
	@echo "Cleanup completed."