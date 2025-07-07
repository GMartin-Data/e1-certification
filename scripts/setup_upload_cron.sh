#!/bin/bash
# Set up cron job for automatic Excel uploads to S3

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🕐 Setting up cron job for Excel uploads..."
echo "Project root: $PROJECT_ROOT"

# Create the cron command
# Runs every Sunday at 1:00 AM
CRON_COMMAND="0 1 * * 0 cd $PROJECT_ROOT && $PROJECT_ROOT/.venv/bin/python $PROJECT_ROOT/scripts/upload_to_s3.py >> $PROJECT_ROOT/logs/upload_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "upload_to_s3.py"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    # Remove existing entry
    crontab -l 2>/dev/null | grep -v "upload_to_s3.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

echo "✅ Cron job installed successfully!"
echo ""
echo "📋 Cron schedule: Every Sunday at 1:00 AM"
echo "📁 Log file: $PROJECT_ROOT/logs/upload_cron.log"
echo ""
echo "🔍 To verify, run: crontab -l"
echo "❌ To remove, run: crontab -l | grep -v 'upload_to_s3.py' | crontab -"
