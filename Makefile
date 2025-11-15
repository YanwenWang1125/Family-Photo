# Makefile for common development tasks

.PHONY: help backend-install frontend-install install dev-up dev-down test lint format clean

help:
	@echo "Family Photo Hub - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install all dependencies (backend + frontend)"
	@echo "  make backend-install  - Install backend dependencies"
	@echo "  make frontend-install - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up          - Start all services with docker-compose"
	@echo "  make dev-down        - Stop all services"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test            - Run all tests"
	@echo "  make lint            - Run linters"
	@echo "  make format          - Format code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           - Remove build artifacts and cache"

# Installation
backend-install:
	cd backend && pip install -e ".[dev]"

frontend-install:
	cd frontend && npm install

install: backend-install frontend-install

# Development
dev-up:
	docker-compose up -d

dev-down:
	docker-compose down

# Testing
test:
	cd backend && pytest
	cd frontend && npm test

# Code quality
lint:
	cd backend && ruff check . && mypy .
	cd frontend && npm run lint

format:
	cd backend && black . && isort .
	cd frontend && npm run format || echo "Add format script to package.json"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
