#!/bin/bash

# Setup script for systemd service to keep backend running persistently
# Run this script on your Ubuntu EC2 instance

set -e

echo "🚀 Setting up systemd service for Nifty Backend..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

# Detect user (try common EC2 user names)
if [ -d "/home/ubuntu" ]; then
    USER="ubuntu"
elif [ -d "/home/ec2-user" ]; then
    USER="ec2-user"
else
    USER=$(whoami)
fi

echo "📁 Detected project directory: $PROJECT_ROOT"
echo "📁 Backend directory: $BACKEND_DIR"
echo "👤 Using user: $USER"

# Check if server.py exists
if [ ! -f "$BACKEND_DIR/server.py" ]; then
    echo "❌ server.py not found at $BACKEND_DIR/server.py"
    echo "   Current directory: $(pwd)"
    echo "   Please run this script from the backend directory or ensure server.py exists"
    exit 1
fi

# Find Python executable and virtual environment
PYTHON_EXEC=""
VENV_DIR=""

# Check common venv locations (including .venv variants)
VENV_LOCATIONS=(
    "$BACKEND_DIR/.venv"
    "$BACKEND_DIR/venv"
    "$BACKEND_DIR/backend/.venv"
    "$BACKEND_DIR/backend/venv"
    "$PROJECT_ROOT/.venv"
    "$PROJECT_ROOT/venv"
    "$PROJECT_ROOT/backend/.venv"
    "$PROJECT_ROOT/backend/venv"
    "$PROJECT_ROOT/backend/backend/.venv"
    "$PROJECT_ROOT/backend/backend/venv"
    "$HOME/.venv"
    "$HOME/venv"
)

echo "🔍 Looking for virtual environment..."
for venv_path in "${VENV_LOCATIONS[@]}"; do
    if [ -d "$venv_path" ] && [ -f "$venv_path/bin/python3" ]; then
        VENV_DIR="$venv_path"
        PYTHON_EXEC="$venv_path/bin/python3"
        echo "✅ Found virtual environment at: $VENV_DIR"
        
        # Check if uvicorn is installed, if not install dependencies
        if ! "$PYTHON_EXEC" -m pip show uvicorn &> /dev/null; then
            echo "⚠️  uvicorn not found in venv, installing dependencies..."
            "$PYTHON_EXEC" -m pip install --upgrade pip --quiet
            if [ -f "$BACKEND_DIR/requirements.txt" ]; then
                echo "   Installing from requirements.txt..."
                "$PYTHON_EXEC" -m pip install -r "$BACKEND_DIR/requirements.txt" --quiet
            else
                echo "   requirements.txt not found, installing uvicorn and fastapi..."
                "$PYTHON_EXEC" -m pip install uvicorn fastapi --quiet
            fi
            echo "✅ Dependencies installed"
        else
            echo "✅ Dependencies already installed"
        fi
        break
    fi
done

# If venv not found, create one automatically
if [ -z "$PYTHON_EXEC" ]; then
    echo "⚠️  Virtual environment not found in common locations"
    
    # Check if system python3 is available
    if command -v python3 &> /dev/null; then
        SYSTEM_PYTHON=$(which python3)
        echo "💡 Found system Python at: $SYSTEM_PYTHON"
        echo "📦 Creating virtual environment at $BACKEND_DIR/venv..."
        
        python3 -m venv "$BACKEND_DIR/venv"
        VENV_DIR="$BACKEND_DIR/venv"
        PYTHON_EXEC="$VENV_DIR/bin/python3"
        
        if [ ! -f "$PYTHON_EXEC" ]; then
            echo "❌ Failed to create virtual environment"
            exit 1
        fi
        
        echo "📥 Installing dependencies..."
        "$PYTHON_EXEC" -m pip install --upgrade pip --quiet
        if [ -f "$BACKEND_DIR/requirements.txt" ]; then
            echo "   Installing from requirements.txt..."
            "$PYTHON_EXEC" -m pip install -r "$BACKEND_DIR/requirements.txt" --quiet
        else
            echo "   requirements.txt not found, installing uvicorn and fastapi..."
            "$PYTHON_EXEC" -m pip install uvicorn fastapi --quiet
        fi
        echo "✅ Virtual environment created and dependencies installed"
    else
        echo "❌ Python3 not found. Please install Python3 first."
        exit 1
    fi
fi

# Verify Python executable exists
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "❌ Python executable not found at: $PYTHON_EXEC"
    exit 1
fi

echo "🐍 Using Python: $PYTHON_EXEC"

# Create systemd service file
SERVICE_FILE="/tmp/nifty-backend.service"

# Set PATH based on whether venv exists
if [ -n "$VENV_DIR" ]; then
    ENV_PATH="$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
else
    ENV_PATH="/usr/local/bin:/usr/bin:/bin"
fi

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Nifty Backend FastAPI Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$ENV_PATH"
ExecStart=$PYTHON_EXEC -m uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nifty-backend

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "📝 Created service file: $SERVICE_FILE"
echo ""
echo "📋 Service file contents:"
cat "$SERVICE_FILE"
echo ""

# Copy service file to systemd directory
echo "📦 Copying service file to systemd directory..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/nifty-backend.service

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service to start on boot..."
sudo systemctl enable nifty-backend.service

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Start the service: sudo systemctl start nifty-backend"
echo "   2. Check status: sudo systemctl status nifty-backend"
echo "   3. View logs: sudo journalctl -u nifty-backend -f"
echo "   4. Stop the service: sudo systemctl stop nifty-backend"
echo "   5. Restart the service: sudo systemctl restart nifty-backend"
echo ""
echo "💡 The service will automatically restart if it crashes and start on system boot."

