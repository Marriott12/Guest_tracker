#!/bin/bash
# Quick Deployment Script for cPanel Server
# Run this after SSH into: envithcy@server219.web-hosting.com

echo "=========================================="
echo "Starting Deployment to cPanel Server"
echo "=========================================="

# Navigate to project directory
echo "Step 1: Navigating to project directory..."
cd ~/public_html/guest_tracker || { echo "Failed to navigate to project directory"; exit 1; }

# Pull latest changes
echo "Step 2: Pulling latest changes from GitHub..."
git pull origin main || { echo "Failed to pull from GitHub"; exit 1; }

# Activate virtual environment
echo "Step 3: Activating virtual environment..."
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Install/Update dependencies
echo "Step 4: Installing/updating dependencies..."
pip install -r requirements_clean.txt || { echo "Failed to install dependencies"; exit 1; }

# Verify django-recaptcha version
echo "Step 5: Verifying django-recaptcha version..."
RECAPTCHA_VERSION=$(pip show django-recaptcha | grep Version | awk '{print $2}')
echo "django-recaptcha version: $RECAPTCHA_VERSION"
if [ "$RECAPTCHA_VERSION" != "3.0.0" ]; then
    echo "WARNING: django-recaptcha should be version 3.0.0, found $RECAPTCHA_VERSION"
    echo "Fixing version..."
    pip uninstall django-recaptcha -y
    pip install django-recaptcha==3.0.0
fi

# Run migrations
echo "Step 6: Running database migrations..."
python manage.py migrate || { echo "Failed to run migrations"; exit 1; }

# Collect static files
echo "Step 7: Collecting static files..."
python manage.py collectstatic --noinput || { echo "Failed to collect static files"; exit 1; }

# Check deployment settings
echo "Step 8: Checking deployment configuration..."
python manage.py check --deploy

# Restart application
echo "Step 9: Restarting application..."
touch ~/public_html/guest_tracker/tmp/restart.txt

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with production settings if not done yet"
echo "2. Visit https://guests.envisagezm.com to verify"
echo "3. Check logs: tail -f logs/django.log"
echo ""
