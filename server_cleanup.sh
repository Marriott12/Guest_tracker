#!/bin/bash
# Remote Server Cleanup Script
# Run this on the cPanel server after pulling the latest changes

echo "=== Guest Tracker Remote Cleanup ==="

# Navigate to project directory
cd ~/public_html/guest_tracker || exit

echo "Pulling latest changes from GitHub..."
git pull origin main

echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

echo "Removing staticfiles directory..."
rm -rf staticfiles/

echo "Removing backups directory..."
rm -rf backups/

echo "Activating virtual environment..."
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements_clean.txt

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting application..."
mkdir -p ~/public_html/guest_tracker/tmp
touch ~/public_html/guest_tracker/tmp/restart.txt

echo ""
echo "=== Cleanup Complete ==="
echo "Repository cleaned and application updated!"
echo "Visit: https://guests.envisagezm.com to verify"
