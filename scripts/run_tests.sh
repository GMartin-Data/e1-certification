#!/bin/bash
# Run database tests with different configurations

echo "🧪 Running e1-certification database tests..."
echo "==========================================="

# Run all tests
if [ "$1" == "all" ]; then
    echo "Running all tests..."
    pytest -v

# Run only unit tests (fast)
elif [ "$1" == "unit" ]; then
    echo "Running unit tests only..."
    pytest -v -m "not integration"

# Run only integration tests
elif [ "$1" == "integration" ]; then
    echo "Running integration tests only..."
    pytest -v -m integration

# Run with coverage
elif [ "$1" == "coverage" ]; then
    echo "Running tests with coverage..."
    pytest --cov=e1_certification.db --cov-report=html --cov-report=term

# Show usage
else
    echo "Usage: ./scripts/run_tests.sh [all|unit|integration|coverage]"
    echo ""
    echo "Options:"
    echo "  all          - Run all tests"
    echo "  unit         - Run unit tests only (fast)"
    echo "  integration  - Run integration tests only"
    echo "  coverage     - Run with coverage report"
    echo ""
    echo "Running unit tests by default..."
    pytest -v -m "not integration"
fi
