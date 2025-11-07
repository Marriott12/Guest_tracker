#!/bin/bash
# Automated cPanel Deployment Script
# Zambia Army Guest Tracking System
#
# Prerequisites (MUST be done manually in cPanel first):
# 1. Created Python App in cPanel
# 2. Created MySQL database and user
# 3. Uploaded project files to server
# 4. Have your database credentials ready
#
# Usage: bash cpanel_auto_deploy.sh

set -e  # Exit on any error

echo "=========================================="
echo "  Zambia Army Guest Tracker Auto Deploy  "
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Get user input
echo "This script will help you deploy your Django application to cPanel."
echo ""
print_info "Please have the following information ready:"
echo "  - Virtual environment path (from cPanel Python App setup)"
echo "  - MySQL database name"
echo "  - MySQL database user"
echo "  - MySQL database password"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Get cPanel username
print_info "Getting cPanel username..."
CPANEL_USER=$(whoami)
print_success "Username: $CPANEL_USER"
echo ""

# Get home directory
HOME_DIR="/home/$CPANEL_USER"
print_info "Home directory: $HOME_DIR"
echo ""

# Ask for project directory
read -p "Enter your project directory name [guest_tracker]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-guest_tracker}
PROJECT_PATH="$HOME_DIR/$PROJECT_DIR"

if [ ! -d "$PROJECT_PATH" ]; then
    print_error "Project directory not found: $PROJECT_PATH"
    echo "Please upload your project files first."
    exit 1
fi

print_success "Project found at: $PROJECT_PATH"
cd "$PROJECT_PATH"
echo ""

# Ask for virtual environment path
echo "Example: /home/$CPANEL_USER/virtualenv/guest_tracker/3.11"
read -p "Enter virtual environment path: " VENV_PATH

if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found: $VENV_PATH"
    echo "Please create Python App in cPanel first."
    exit 1
fi

print_success "Virtual environment found"
echo ""

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
print_success "Virtual environment activated"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version)
print_info "Python version: $PYTHON_VERSION"
echo ""

# Get database credentials
print_info "Enter MySQL database credentials:"
read -p "Database name (e.g., ${CPANEL_USER}_guesttracker): " DB_NAME
read -p "Database user (e.g., ${CPANEL_USER}_dbuser): " DB_USER
read -sp "Database password: " DB_PASSWORD
echo ""
read -p "Database host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}
read -p "Database port [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}
echo ""

# Get domain
read -p "Enter your domain (e.g., yourdomain.com): " DOMAIN
echo ""

# Get email configuration
read -p "Configure email now? (y/n) [n]: " CONFIGURE_EMAIL
CONFIGURE_EMAIL=${CONFIGURE_EMAIL:-n}

if [ "$CONFIGURE_EMAIL" = "y" ]; then
    read -p "SMTP Host (e.g., smtp.gmail.com): " EMAIL_HOST
    read -p "SMTP Port [587]: " EMAIL_PORT
    EMAIL_PORT=${EMAIL_PORT:-587}
    read -p "Email address: " EMAIL_USER
    read -sp "Email password/app password: " EMAIL_PASSWORD
    echo ""
    read -p "From email address: " FROM_EMAIL
    echo ""
fi

# Generate SECRET_KEY
print_info "Generating Django SECRET_KEY..."
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
print_success "SECRET_KEY generated"
echo ""

# Create .env file
print_info "Creating .env file..."
cat > .env << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# Email Configuration
EOF

if [ "$CONFIGURE_EMAIL" = "y" ]; then
    cat >> .env << EOF
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=$EMAIL_PORT
EMAIL_USE_TLS=True
EMAIL_HOST_USER=$EMAIL_USER
EMAIL_HOST_PASSWORD=$EMAIL_PASSWORD
DEFAULT_FROM_EMAIL=$FROM_EMAIL
EOF
else
    cat >> .env << EOF
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@zambiaarmyevents.com
EOF
fi

cat >> .env << EOF

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Time Zone
TIME_ZONE=Africa/Lusaka

# Media and Static Files
MEDIA_ROOT=media
STATIC_ROOT=staticfiles

# reCAPTCHA Keys (Leave empty for now)
RECAPTCHA_PUBLIC_KEY=
RECAPTCHA_PRIVATE_KEY=
EOF

print_success ".env file created"
echo ""

# Create passenger_wsgi.py
print_info "Creating passenger_wsgi.py..."
cat > passenger_wsgi.py << EOF
import os
import sys

# Add your project directory to the sys.path
project_home = '$PROJECT_PATH'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'guest_tracker.settings'

# Activate virtual environment
activate_this = '$VENV_PATH/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

# Import Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF

print_success "passenger_wsgi.py created"
echo ""

# Install MySQL client
print_info "Installing MySQL client..."
pip install mysqlclient 2>/dev/null || {
    print_info "mysqlclient failed, trying pymysql..."
    pip install pymysql
    
    # Add pymysql configuration to __init__.py
    INIT_FILE="guest_tracker/__init__.py"
    if ! grep -q "pymysql" "$INIT_FILE" 2>/dev/null; then
        cat >> "$INIT_FILE" << EOF

# Use PyMySQL as MySQLdb
import pymysql
pymysql.install_as_MySQLdb()
EOF
        print_success "Added pymysql configuration"
    fi
}
print_success "MySQL client installed"
echo ""

# Install dependencies
print_info "Installing project dependencies (this may take several minutes)..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies installed"
echo ""

# Run migrations
print_info "Running database migrations..."
python manage.py migrate
print_success "Migrations completed"
echo ""

# Create superuser
print_info "Creating superuser account..."
echo ""
echo "Please enter superuser details:"
python manage.py createsuperuser
echo ""
print_success "Superuser created"
echo ""

# Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"
echo ""

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p media logs backups/database
touch logs/django.log
print_success "Directories created"
echo ""

# Set permissions
print_info "Setting file permissions..."
chmod 755 "$PROJECT_PATH"
chmod 644 .env
chmod 644 passenger_wsgi.py
chmod 755 media logs backups
print_success "Permissions set"
echo ""

# Display completion message
echo ""
echo "=========================================="
print_success "DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure Static Files in cPanel Python App:"
echo "   - Go to cPanel > Setup Python App > Edit your app"
echo "   - Add Static File mappings:"
echo "     URL: /static    Path: $PROJECT_PATH/staticfiles"
echo "     URL: /media     Path: $PROJECT_PATH/media"
echo ""
echo "2. Restart your application:"
echo "   - In cPanel > Setup Python App > Click 'Restart' button"
echo ""
echo "3. Install SSL certificate:"
echo "   - Go to cPanel > SSL/TLS Status"
echo "   - Run AutoSSL for $DOMAIN"
echo ""
echo "4. Test your application:"
echo "   - Visit: https://$DOMAIN"
echo "   - Admin: https://$DOMAIN/admin"
echo ""
echo "Important information saved:"
echo "  - Configuration: $PROJECT_PATH/.env"
echo "  - WSGI file: $PROJECT_PATH/passenger_wsgi.py"
echo ""
print_info "Keep your database credentials and superuser password safe!"
echo ""
echo "For troubleshooting, check:"
echo "  - Error logs in cPanel > Setup Python App > Log files"
echo "  - Django logs: $PROJECT_PATH/logs/django.log"
echo ""
echo "=========================================="
