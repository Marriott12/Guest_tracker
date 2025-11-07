#!/bin/bash
# Guest Tracker - cPanel Deployment Setup Script
# This script helps set up the Guest Tracker application on cPanel hosting

echo "========================================="
echo "Guest Tracker - cPanel Deployment Setup"
echo "========================================="
echo ""

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Current directory: $SCRIPT_DIR"
echo ""

# Step 1: Check if git repository exists
echo "Step 1: Checking Git repository..."
if [ -d ".git" ]; then
    echo "✓ Git repository found"
    echo "Pulling latest changes..."
    git pull origin main
else
    echo "✗ Not a git repository"
    echo ""
    echo "To initialize git repository, run these commands:"
    echo "  git init"
    echo "  git remote add origin https://github.com/Marriott12/Guest_tracker.git"
    echo "  git fetch origin"
    echo "  git checkout main"
    echo "  git pull origin main"
    echo ""
    read -p "Would you like to initialize git now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        git remote add origin https://github.com/Marriott12/Guest_tracker.git
        git fetch origin
        git checkout -b main
        git pull origin main
        echo "✓ Git repository initialized"
    else
        echo "⚠ Skipping git initialization"
    fi
fi
echo ""

# Step 2: Check Python version
echo "Step 2: Checking Python installation..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✓ Python 3.11 found: $(python3.11 --version)"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✓ Python 3 found: $(python3 --version)"
    echo "⚠ Warning: Python 3.11 is recommended"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✓ Python found: $(python --version)"
    echo "⚠ Warning: Python 3.11 is recommended"
else
    echo "✗ Python not found!"
    echo "Please install Python 3.11 or contact your hosting provider"
    exit 1
fi
echo ""

# Step 3: Check/Create Virtual Environment
echo "Step 3: Checking virtual environment..."
VENV_PATHS=(
    ".venv"
    "../../../virtualenv/public_html/guest_tracker/3.11"
    "$HOME/virtualenv/public_html/guest_tracker/3.11"
)

VENV_FOUND=false
for VENV_PATH in "${VENV_PATHS[@]}"; do
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo "✓ Virtual environment found at: $VENV_PATH"
        VENV_ACTIVATE="$VENV_PATH/bin/activate"
        VENV_FOUND=true
        break
    fi
done

if [ "$VENV_FOUND" = false ]; then
    echo "✗ Virtual environment not found"
    echo ""
    read -p "Would you like to create a virtual environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        $PYTHON_CMD -m venv .venv
        VENV_ACTIVATE=".venv/bin/activate"
        echo "✓ Virtual environment created at .venv"
    else
        echo "⚠ Skipping virtual environment creation"
        echo "You'll need to create it manually before proceeding"
        exit 1
    fi
fi
echo ""

# Step 4: Activate virtual environment and check pip
echo "Step 4: Activating virtual environment..."
source "$VENV_ACTIVATE"
echo "✓ Virtual environment activated"
echo ""

# Step 5: Upgrade pip
echo "Step 5: Upgrading pip..."
pip install --upgrade pip
echo "✓ Pip upgraded"
echo ""

# Step 6: Install dependencies
echo "Step 6: Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "✗ requirements.txt not found!"
    exit 1
fi
echo ""

# Step 7: Check .env file
echo "Step 7: Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    echo ""
    echo "⚠ IMPORTANT: Please verify your .env file contains:"
    echo "  - SECRET_KEY (production secret)"
    echo "  - DEBUG=False"
    echo "  - ALLOWED_HOSTS (your domain)"
    echo "  - Database credentials (MySQL)"
    echo "  - Email configuration (SMTP)"
    echo "  - reCAPTCHA keys"
    echo ""
    read -p "Press Enter to continue after verifying .env file..."
else
    echo "✗ .env file not found"
    if [ -f ".env.example" ]; then
        echo ""
        read -p "Would you like to create .env from .env.example? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            echo "✓ .env file created from .env.example"
            echo ""
            echo "⚠ IMPORTANT: Edit .env file with your production settings!"
            echo "Run: nano .env"
            exit 0
        fi
    else
        echo "✗ .env.example not found either!"
        exit 1
    fi
fi
echo ""

# Step 8: Run migrations
echo "Step 8: Running database migrations..."
python manage.py migrate
echo "✓ Migrations completed"
echo ""

# Step 9: Collect static files
echo "Step 9: Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"
echo ""

# Step 10: Create superuser
echo "Step 10: Create superuser (admin account)..."
read -p "Would you like to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    echo "✓ Superuser created"
else
    echo "⚠ Skipping superuser creation"
    echo "You can create one later with: python manage.py createsuperuser"
fi
echo ""

# Step 11: Check deployment settings
echo "Step 11: Checking deployment configuration..."
python manage.py check --deploy
echo ""

# Final instructions
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Verify your .env file has all production settings"
echo "2. Test the application locally: python manage.py runserver"
echo "3. In cPanel, go to 'Setup Python App' and restart your application"
echo "4. Visit your website and verify everything works"
echo "5. Test these features:"
echo "   - Guest registration with reCAPTCHA"
echo "   - Login with reCAPTCHA"
echo "   - Admin interface (/admin/)"
echo "   - Email sending"
echo ""
echo "To activate virtual environment manually:"
echo "  source $VENV_ACTIVATE"
echo ""
echo "For troubleshooting, see: CPANEL_DEPLOYMENT_GUIDE.md"
echo "========================================="
