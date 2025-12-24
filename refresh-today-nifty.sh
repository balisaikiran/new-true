#!/bin/bash
# Shell script to refresh today's NIFTY data
# Usage: ./refresh-today-nifty.sh [NIFTY 50|NIFTY BANK]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"

# Change to backend directory
cd "$BACKEND_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Get index name from argument if provided
INDEX_ARG=""
if [ -n "$1" ]; then
    if [ "$1" == "NIFTY 50" ] || [ "$1" == "NIFTY BANK" ]; then
        INDEX_ARG="--index \"$1\""
    else
        echo "❌ Error: Invalid index name. Must be 'NIFTY 50' or 'NIFTY BANK'"
        exit 1
    fi
fi

# Run the Python script
echo "🔄 Refreshing today's NIFTY data..."
echo ""

if [ -n "$INDEX_ARG" ]; then
    python3 refresh_today_nifty.py --index "$1"
else
    python3 refresh_today_nifty.py
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Refresh completed successfully!"
else
    echo ""
    echo "❌ Refresh failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE

