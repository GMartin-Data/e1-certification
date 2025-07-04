# e1-certification

AWS Serverless ETL pipeline and REST API for Excel to MySQL data transformation.

## Overview

This project implements:

- Automated Excel to MySQL data pipeline using AWS Lambda
- REST API with authentication for database operations
- Infrastructure as Code using AWS SAM

## Project Status

🚧 Under Development - Phase 1: Foundation Setup

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

Run tests:

```bash
pytest
```

Check code quality:

```bash
ruff check .
ruff format .
```

## Author

Grégory MARTIN
