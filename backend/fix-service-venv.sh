#!/bin/bash

# Quick fix script to update the systemd service with the correct venv path
# Use this if your venv is in a non-standard location

set -e

VENV_PATH="/home/ubuntu/new-true/backend/.venv"

echo "🔧 Fixing systemd service with venv path: $VENV_PATH"

# Verify venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at: $VENV_PATH"
    echo "   Please update VENV_PATH in this script to match your actual venv location"
    exit 1
fi

if [ ! -f "$VENV_PATH/bin/python3" ]; then
    echo "❌ Python executable not found at: $VENV_PATH/bin/python3"
    exit 1
fi

echo "✅ Found virtual environment"

# Detect backend directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"

# Detect user
if [ -d "/home/ubuntu" ]; then
    USER="ubuntu"
elif [ -d "/home/ec2-user" ]; then
    USER="ec2-user"
else
    USER=$(whoami)
fi

echo "📁 Backend directory: $BACKEND_DIR"
echo "👤 User: $USER"

# Create updated service file
SERVICE_FILE="/tmp/nifty-backend.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Nifty Backend FastAPI Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_PATH/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
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

echo "📝 Created updated service file"
echo ""
echo "📋 Service file contents:"
cat "$SERVICE_FILE"
echo ""

# Stop existing service if running
echo "🛑 Stopping existing service..."
sudo systemctl stop nifty-backend.service 2>/dev/null || true

# Copy service file
echo "📦 Installing updated service file..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/nifty-backend.service

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
echo "✅ Enabling service..."
sudo systemctl enable nifty-backend.service

# Start service
echo "🚀 Starting service..."
sudo systemctl start nifty-backend.service

echo ""
echo "✨ Service updated and started!"
echo ""
echo "📊 Check status:"
echo "   sudo systemctl status nifty-backend"
echo ""
echo "📋 View logs:"
echo "   sudo journalctl -u nifty-backend -f"

