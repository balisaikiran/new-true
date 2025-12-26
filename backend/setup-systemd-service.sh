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
echo "👤 Using user: $USER"

# Check if virtual environment exists
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $BACKEND_DIR/venv"
    echo "   Please create it first: python3 -m venv venv"
    exit 1
fi

# Check if server.py exists
if [ ! -f "$BACKEND_DIR/server.py" ]; then
    echo "❌ server.py not found at $BACKEND_DIR/server.py"
    exit 1
fi

# Create systemd service file
SERVICE_FILE="/tmp/nifty-backend.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Nifty Backend FastAPI Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$BACKEND_DIR/venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
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

