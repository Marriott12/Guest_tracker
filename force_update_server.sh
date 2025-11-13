#!/bin/bash
# Force Update Server Script
# This script will update the cPanel server to exactly match the GitHub repository
# WARNING: This will overwrite any local changes on the server!

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     FORCE UPDATE SERVER TO MATCH REPOSITORY               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR=~/public_html/guest_tracker
VENV_PATH=/home/envithcy/virtualenv/guest_tracker/3.11

echo -e "${CYAN}Step 1: Navigating to project directory...${NC}"
cd $PROJECT_DIR || exit 1
echo -e "${GREEN}✓ In directory: $(pwd)${NC}"
echo ""

# Backup critical files that shouldn't be in git
echo -e "${CYAN}Step 2: Backing up critical files...${NC}"
BACKUP_DIR=$(mktemp -d)
echo "Backup directory: $BACKUP_DIR"

if [ -f "passenger_wsgi.py" ]; then
    cp passenger_wsgi.py "$BACKUP_DIR/passenger_wsgi.py"
    echo -e "${GREEN}✓ Backed up passenger_wsgi.py${NC}"
fi

if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env"
    echo -e "${GREEN}✓ Backed up .env${NC}"
fi

if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "$BACKUP_DIR/db.sqlite3"
    echo -e "${GREEN}✓ Backed up db.sqlite3${NC}"
fi

if [ -d "media" ]; then
    cp -r media "$BACKUP_DIR/media"
    echo -e "${GREEN}✓ Backed up media directory${NC}"
fi

if [ -d "logs" ]; then
    cp -r logs "$BACKUP_DIR/logs"
    echo -e "${GREEN}✓ Backed up logs directory${NC}"
fi
echo ""

# Fetch latest from repository
echo -e "${CYAN}Step 3: Fetching latest changes from GitHub...${NC}"
git fetch origin
echo -e "${GREEN}✓ Fetched from origin${NC}"
echo ""

# Reset to match repository exactly
echo -e "${YELLOW}Step 4: Resetting to match repository (this will overwrite local changes)...${NC}"
git reset --hard origin/main
echo -e "${GREEN}✓ Reset to origin/main${NC}"
echo ""

# Clean untracked files
echo -e "${CYAN}Step 5: Cleaning untracked files...${NC}"
git clean -fd
echo -e "${GREEN}✓ Cleaned untracked files${NC}"
echo ""

# Restore critical files
echo -e "${CYAN}Step 6: Restoring critical files...${NC}"
if [ -f "$BACKUP_DIR/passenger_wsgi.py" ]; then
    cp "$BACKUP_DIR/passenger_wsgi.py" passenger_wsgi.py
    echo -e "${GREEN}✓ Restored passenger_wsgi.py${NC}"
fi

if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" .env
    echo -e "${GREEN}✓ Restored .env${NC}"
fi

if [ -f "$BACKUP_DIR/db.sqlite3" ]; then
    cp "$BACKUP_DIR/db.sqlite3" db.sqlite3
    echo -e "${GREEN}✓ Restored db.sqlite3${NC}"
fi

if [ -d "$BACKUP_DIR/media" ]; then
    cp -r "$BACKUP_DIR/media" .
    echo -e "${GREEN}✓ Restored media directory${NC}"
fi

if [ -d "$BACKUP_DIR/logs" ]; then
    cp -r "$BACKUP_DIR/logs" .
    echo -e "${GREEN}✓ Restored logs directory${NC}"
fi
echo ""

# Remove Python cache files
echo -e "${CYAN}Step 7: Removing Python cache files...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Removed cache files${NC}"
echo ""

# Activate virtual environment
echo -e "${CYAN}Step 8: Activating virtual environment...${NC}"
source $VENV_PATH/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install/update dependencies
echo -e "${CYAN}Step 9: Installing/updating dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements_clean.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run migrations
echo -e "${CYAN}Step 10: Running database migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ Migrations complete${NC}"
echo ""

# Collect static files
echo -e "${CYAN}Step 11: Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

# Create necessary directories
echo -e "${CYAN}Step 12: Creating necessary directories...${NC}"
mkdir -p tmp
mkdir -p media/qr_codes
mkdir -p media/barcodes
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Set permissions
echo -e "${CYAN}Step 13: Setting permissions...${NC}"
chmod -R 755 .
chmod 644 .env 2>/dev/null || true
chmod -R 775 media 2>/dev/null || true
chmod -R 775 logs 2>/dev/null || true
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# Run deployment checks
echo -e "${CYAN}Step 14: Running deployment checks...${NC}"
python manage.py check --deploy 2>&1 | head -20
echo ""

# Restart application
echo -e "${CYAN}Step 15: Restarting application...${NC}"
touch tmp/restart.txt
echo -e "${GREEN}✓ Application restart triggered${NC}"
echo ""

# Show current commit
echo -e "${CYAN}Current deployment:${NC}"
git log -1 --pretty=format:"Commit: %h%nAuthor: %an%nDate: %ad%nMessage: %s" --date=short
echo ""
echo ""

# Cleanup backup directory
echo -e "${CYAN}Step 16: Cleaning up temporary files...${NC}"
rm -rf "$BACKUP_DIR"
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              UPDATE COMPLETED SUCCESSFULLY!                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✓ Server is now synchronized with GitHub repository${NC}"
echo -e "${CYAN}✓ Visit: ${YELLOW}https://guests.envisagezm.com${NC}"
echo ""
echo "To view application logs:"
echo "  tail -f logs/django.log"
echo ""
