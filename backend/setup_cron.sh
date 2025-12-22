#!/bin/bash
# Setup cron job for daily NIFTY data update at 3:35 PM IST (10:05 AM UTC)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/.venv/bin/python3"
SCRIPT_PATH="$SCRIPT_DIR/daily_nifty_update_nse.py"
LOG_PATH="$SCRIPT_DIR/logs/daily_nifty_update.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Make script executable
chmod +x "$SCRIPT_PATH"

# Create cron job entry
# 3:35 PM IST = 10:05 AM UTC (IST is UTC+5:30)
CRON_JOB="5 10 * * 1-5 cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "Schedule: Daily at 3:35 PM IST (10:05 AM UTC), Monday-Friday"
echo "Script: $SCRIPT_PATH"
echo "Logs: $LOG_PATH"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"
echo ""
echo "To test the script manually:"
echo "  cd $SCRIPT_DIR"
echo "  source .venv/bin/activate"
echo "  python3 daily_nifty_update_nse.py"
