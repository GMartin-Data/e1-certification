#!/bin/bash
# Set up local development environment

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get project root (parent of scripts directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up e1-certification local environment..."

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if .env exists
if [[ ! -f .env ]]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual values!"
else
    echo "✅ .env already exists"
fi

# Check virtual environment
if [[ -d .venv ]]; then
    echo "✅ Virtual environment found at $PROJECT_ROOT/.venv"
    echo "🐍 To activate it, run: source .venv/bin/activate"
else
    echo "❌ Virtual environment not found. Run 'uv venv' first!"
    exit 1
fi

echo "✨ Setup complete! Don't forget to update your .env file."
