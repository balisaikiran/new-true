# EC2 Systemd Service Setup Guide

This guide helps you set up your FastAPI backend to run as a systemd service on your Ubuntu EC2 instance. This ensures the server:
- ✅ Runs persistently (survives SSH disconnects)
- ✅ Automatically restarts if it crashes
- ✅ Starts automatically on system boot
- ✅ Runs in the background as a daemon

## Problem

When you run `python3 -m uvicorn server:app --host 0.0.0.0 --port 8000` in a terminal, the process gets killed when:
- Your SSH session disconnects
- The terminal closes
- The system reboots

## Solution: Systemd Service

Systemd is the service manager on Ubuntu that runs processes as daemons in the background.

## Quick Setup

### Step 1: SSH into your EC2 instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-instance-ip
```

### Step 2: Navigate to your project directory

```bash
cd ~/app-main-2/backend
# Or wherever your backend directory is located
```

### Step 3: Run the setup script

```bash
chmod +x setup-systemd-service.sh
./setup-systemd-service.sh
```

The script will:
- Detect your project directory and user
- Create a systemd service file
- Install and enable the service
- Configure it to start on boot

### Step 4: Start the service

```bash
sudo systemctl start nifty-backend
```

### Step 5: Verify it's running

```bash
sudo systemctl status nifty-backend
```

You should see `active (running)` in green.

## Manual Setup (Alternative)

If the script doesn't work, you can set it up manually:

### Step 1: Create the service file

```bash
sudo nano /etc/systemd/system/nifty-backend.service
```

### Step 2: Paste this content (adjust paths as needed):

```ini
[Unit]
Description=Nifty Backend FastAPI Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/app-main-2/backend
Environment="PATH=/home/ubuntu/app-main-2/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/app-main-2/backend/venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nifty-backend

[Install]
WantedBy=multi-user.target
```

**Important:** Update these paths to match your setup:
- `User=ubuntu` → Change if you use a different user
- `WorkingDirectory=/home/ubuntu/app-main-2/backend` → Your backend directory path
- `ExecStart=/home/ubuntu/app-main-2/backend/venv/bin/python3` → Path to your Python executable

### Step 3: Reload systemd and enable the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable nifty-backend
sudo systemctl start nifty-backend
```

## Useful Commands

### Check service status
```bash
sudo systemctl status nifty-backend
```

### View logs (live)
```bash
sudo journalctl -u nifty-backend -f
```

### View last 100 lines of logs
```bash
sudo journalctl -u nifty-backend -n 100
```

### Restart the service
```bash
sudo systemctl restart nifty-backend
```

### Stop the service
```bash
sudo systemctl stop nifty-backend
```

### Start the service
```bash
sudo systemctl start nifty-backend
```

### Disable auto-start on boot
```bash
sudo systemctl disable nifty-backend
```

### Enable auto-start on boot
```bash
sudo systemctl enable nifty-backend
```

## Troubleshooting

### Service fails to start

1. **Check the logs:**
   ```bash
   sudo journalctl -u nifty-backend -n 50
   ```

2. **Verify paths are correct:**
   ```bash
   # Check if Python exists at the path
   ls -la /home/ubuntu/app-main-2/backend/venv/bin/python3
   
   # Check if server.py exists
   ls -la /home/ubuntu/app-main-2/backend/server.py
   ```

3. **Check permissions:**
   ```bash
   # Make sure the user has access to the directory
   ls -la /home/ubuntu/app-main-2/backend/
   ```

### Service starts but crashes immediately

1. **Check logs for errors:**
   ```bash
   sudo journalctl -u nifty-backend -n 100 --no-pager
   ```

2. **Test running manually:**
   ```bash
   cd /home/ubuntu/app-main-2/backend
   source venv/bin/activate
   python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```

3. **Check if port 8000 is already in use:**
   ```bash
   sudo netstat -tulpn | grep 8000
   # Or
   sudo lsof -i :8000
   ```

### Port already in use

If port 8000 is already in use, you can either:
1. Stop the existing process:
   ```bash
   sudo lsof -i :8000
   # Find the PID and kill it
   sudo kill -9 <PID>
   ```

2. Or change the port in the service file:
   ```bash
   sudo nano /etc/systemd/system/nifty-backend.service
   # Change --port 8000 to --port 8001
   sudo systemctl daemon-reload
   sudo systemctl restart nifty-backend
   ```

### Environment variables not loading

If your app needs environment variables from a `.env` file:

1. **Option 1: Add EnvironmentFile to service:**
   ```bash
   sudo nano /etc/systemd/system/nifty-backend.service
   ```
   
   Add this line in the `[Service]` section:
   ```ini
   EnvironmentFile=/home/ubuntu/app-main-2/backend/.env
   ```

2. **Option 2: Add individual Environment variables:**
   ```ini
   Environment="MONGO_URL=your-mongo-url"
   Environment="DB_NAME=your-db-name"
   ```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart nifty-backend
```

## Removing the Service

If you want to remove the systemd service:

```bash
sudo systemctl stop nifty-backend
sudo systemctl disable nifty-backend
sudo rm /etc/systemd/system/nifty-backend.service
sudo systemctl daemon-reload
```

## Benefits

✅ **Persistent**: Server keeps running even after SSH disconnects  
✅ **Auto-restart**: Automatically restarts if it crashes  
✅ **Boot persistence**: Starts automatically when EC2 reboots  
✅ **Logging**: All logs are captured in systemd journal  
✅ **Resource management**: Systemd manages the process lifecycle  

## Notes

- The service runs without the `--reload` flag (which is for development)
- Logs are available via `journalctl` instead of terminal output
- The service runs as the specified user (not root) for security
- You can still access your API at `http://your-ec2-ip:8000`

