# e1-certification

AWS Serverless ETL pipeline and REST API for Excel to MySQL data transformation.

## Overview

This project implements:

- Automated Excel to MySQL data pipeline using AWS Lambda
- REST API with authentication for database operations
- Infrastructure as Code using AWS SAM

## Project Status

🚧 Under Development - Phase 2: Database Layer Complete ✅

## Technology Stack

- **Language**: Python 3.12
- **Cloud**: AWS (Lambda, S3, RDS MySQL, API Gateway)
- **IaC**: AWS SAM
- **API**: FastAPI
- **ORM**: SQLAlchemy 2.0

## Setup Instructions

### Prerequisites

- Python 3.12
- AWS CLI configured with credentials
- SAM CLI installed
- uv package manager

### Quick Start

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd e1-certification
   ```

2. Set up the development environment:

   ```bash
   uv venv
   uv sync --dev
   uv pip install -e .
   ./scripts/setup_local.sh
   ```

3. Configure your environment:

   ```bash
   cp .env.example .env
   # Edit .env with your AWS and database credentials
   ```

4. Deploy infrastructure:
   ```bash
   sam build
   sam deploy --guided
   ```

## Project Structure

```
src/e1_certification/
├── api/          # FastAPI application
├── etl/          # Excel processing logic
├── db/           # Database models and connections
├── utils/        # Shared utilities
└── config.py     # Configuration management
```

## Development

## Development

### Quick Commands

We use a Makefile for common tasks:

```bash
make help         # Show all available commands
make setup        # Initial project setup
make test         # Run all tests
make dev          # Run quick checks (lint + unit tests)
```

### Testing

```bash
make test              # Run all tests
make test-unit         # Run unit tests only (fast)
make test-integration  # Run integration tests only
make test-coverage     # Generate coverage report
```

### Code Quality

```bash
make lint    # Check code style
make format  # Format code
make fix     # Fix issues and format
```

### Database

```bash
make db-check   # Test database connection
make db-create  # Create all tables
make db-reset   # Drop and recreate tables (careful!)
```

### Deployment

```bash
make deploy       # Deploy to AWS (dev)
make deploy-prod  # Deploy to AWS (production)
```

## Author

Grégory MARTIN
