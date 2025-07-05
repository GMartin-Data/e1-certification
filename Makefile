# e1-certification Makefile
# Centralized commands for development, testing, and deployment

.PHONY: help
help: ## Show this help message
	@echo "📚 e1-certification - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ========== Setup Commands ==========
.PHONY: install
install: ## Install all dependencies
	uv sync --dev
	uv pip install -e .
	pre-commit install --install-hooks

.PHONY: setup
setup: install ## Complete development setup
	./scripts/setup_local.sh

# ========== Database Commands ==========
.PHONY: db-check
db-check: ## Check database connection
	python scripts/check_db.py

.PHONY: db-create
db-create: ## Create database tables
	python scripts/test_models.py

.PHONY: db-reset
db-reset: ## Drop and recreate all tables
	@echo "⚠️  This will DELETE all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python -c "from e1_certification.db import Base, get_engine; Base.metadata.drop_all(get_engine()); Base.metadata.create_all(get_engine()); print('✅ Database reset complete')"; \
	fi

# ========== ETL Commands ==========
.PHONY: upload
upload: ## Upload Excel files to S3
	python scripts/upload_to_s3.py

.PHONY: setup-cron
setup-cron: ## Set up cron job for automatic uploads
	./scripts/setup_upload_cron.sh

# ========== Testing Commands ==========
.PHONY: test
test: ## Run all tests
	pytest -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	pytest -v -m "not integration"

.PHONY: test-integration
test-integration: ## Run integration tests only
	pytest -v -m integration

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	pytest --cov=e1_certification --cov-report=html --cov-report=term

.PHONY: test-watch
test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw -- -v

# ========== Code Quality Commands ==========
.PHONY: lint
lint: ## Run linting checks
	ruff check .

.PHONY: format
format: ## Format code
	ruff format .

.PHONY: fix
fix: ## Fix linting issues and format code
	ruff check . --fix
	ruff format .

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks
	pre-commit run --all-files

# ========== SAM/AWS Commands ==========
.PHONY: build
build: ## Build SAM application
	sam build

.PHONY: deploy
deploy: build ## Deploy to AWS (dev environment)
	sam deploy

.PHONY: deploy-prod
deploy-prod: build ## Deploy to AWS (prod environment)
	sam deploy --parameter-overrides Environment=prod

# ========== Cleanup Commands ==========
.PHONY: clean
clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage

.PHONY: clean-all
clean-all: clean ## Clean everything including AWS SAM builds
	rm -rf .aws-sam

# ========== Development Shortcuts ==========
.PHONY: dev
dev: ## Run common development checks
	@echo "🔍 Running development checks..."
	@$(MAKE) lint
	@$(MAKE) test-unit

.PHONY: ci
ci: ## Run CI pipeline locally
	@echo "🚀 Running CI pipeline..."
	@$(MAKE) lint
	@$(MAKE) test
	@echo "✅ CI pipeline passed!"

# Default target
.DEFAULT_GOAL := help
