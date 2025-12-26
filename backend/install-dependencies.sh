#!/bin/bash

# Quick script to install dependencies in the virtual environment
# Run this if the service fails with "No module named uvicorn"

set -e

echo "📦 Installing dependencies..."

# Find virtual environment
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

VENV_LOCATIONS=(
    "$BACKEND_DIR/venv"
    "$PROJECT_ROOT/venv"
    "$PROJECT_ROOT/backend/venv"
    "$HOME/venv"
)

PYTHON_EXEC=""

for venv_path in "${VENV_LOCATIONS[@]}"; do
    if [ -d "$venv_path" ] && [ -f "$venv_path/bin/python3" ]; then
        PYTHON_EXEC="$venv_path/bin/python3"
        echo "✅ Found virtual environment at: $venv_path"
        break
    fi
done

if [ -z "$PYTHON_EXEC" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please create one first: python3 -m venv venv"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
"$PYTHON_EXEC" -m pip install --upgrade pip --quiet

# Install dependencies
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "📥 Installing from requirements.txt..."
    "$PYTHON_EXEC" -m pip install -r "$BACKEND_DIR/requirements.txt"
else
    echo "⚠️  requirements.txt not found, installing uvicorn and fastapi..."
    "$PYTHON_EXEC" -m pip install uvicorn fastapi
fi

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "🔄 Now restart the service:"
echo "   sudo systemctl restart nifty-backend"
echo "   sudo systemctl status nifty-backend"

