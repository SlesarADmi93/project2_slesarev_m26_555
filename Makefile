.PHONY: help install run test lint clean build check-publish

GREEN := \033[0;32m
NC := \033[0m # No Color

help:
	@echo "Доступные команды:"
	@echo "  make install          - Установить зависимости (uv sync)"
	@echo "  make run              - Запустить приложение (uv run database)"
	@echo "  make lint             - Проверка кода линтером Ruff"
	@echo "  make lint-fix         - Автоматическое исправление ошибок Ruff"
	@echo "  make build            - Сборка пакета (uv build)"
	@echo "  make check-publish    - Проверка метаданных перед публикацией"
	@echo "  make clean            - Очистка временных файлов"

install:
	@echo "$(GREEN)Установка зависимостей через uv...$(NC)"
	uv sync

run:
	@echo "$(GREEN)Запуск базы данных...$(NC)"
	uv run database

lint:
	@echo "$(GREEN)Проверка стиля кода (Ruff)...$(NC)"
	uv run ruff check .

lint-fix:
	@echo "$(GREEN)Исправление стиля кода (Ruff)...$(NC)"
	uv run ruff check . --fix

test:
	@echo "$(GREEN)Запуск тестов...$(NC)"
	# Если у вас есть pytest, раскомментируйте строку ниже:
	# uv run pytest
	@echo "Тесты не настроены или отсутствуют."

build:
	@echo "$(GREEN)Сборка пакета...$(NC)"
	uv build

check-publish:
	@echo "$(GREEN)Проверка метаданных пакета...$(NC)"
	uv build
	uvx twine check dist/*

clean:
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -r {} +
	@echo "Очистка завершена."