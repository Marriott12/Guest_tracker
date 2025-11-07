"""
WSGI config for Guest Tracker project - cPanel Passenger deployment

This module contains the WSGI application used by Passenger (cPanel's Python app server).
It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# ============================================================================
# IMPORTANT: Update these paths to match your cPanel environment
# ============================================================================

# Your cPanel username (change 'envithcy' to your actual username)
CPANEL_USER = 'envithcy'

# Project directory path
PROJECT_HOME = f'/home/{CPANEL_USER}/public_html/guest_tracker'

# Virtual environment path (update if using cPanel's virtualenv)
# Option 1: If using cPanel Setup Python App
VIRTUALENV_PATH = f'/home/{CPANEL_USER}/virtualenv/public_html/guest_tracker/3.11'

# Option 2: If using .venv in project directory
# VIRTUALENV_PATH = f'{PROJECT_HOME}/.venv'

# ============================================================================
# Don't change anything below unless you know what you're doing
# ============================================================================

# Add your project directory to the sys.path
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

# Add virtual environment's site-packages to sys.path
PYTHON_VERSION = '3.11'  # Update if using different Python version
virtualenv_site_packages = os.path.join(
    VIRTUALENV_PATH, 
    'lib', 
    f'python{PYTHON_VERSION}', 
    'site-packages'
)

if os.path.exists(virtualenv_site_packages):
    if virtualenv_site_packages not in sys.path:
        sys.path.insert(0, virtualenv_site_packages)
else:
    # Fallback: try to find site-packages
    for item in os.listdir(os.path.join(VIRTUALENV_PATH, 'lib')):
        if item.startswith('python'):
            site_packages = os.path.join(VIRTUALENV_PATH, 'lib', item, 'site-packages')
            if os.path.exists(site_packages):
                sys.path.insert(0, site_packages)
                break

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guest_tracker.settings')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = os.path.join(PROJECT_HOME, '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not installed, environment variables should be set via cPanel
    pass

# Get the Django WSGI application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception as e:
    # Log error for debugging
    import traceback
    error_log = f'/home/{CPANEL_USER}/logs/passenger_error.log'
    try:
        with open(error_log, 'a') as f:
            f.write(f'\n\n{"="*80}\n')
            f.write(f'WSGI Startup Error - {os.path.basename(__file__)}\n')
            f.write(f'{"="*80}\n')
            f.write(f'PROJECT_HOME: {PROJECT_HOME}\n')
            f.write(f'VIRTUALENV_PATH: {VIRTUALENV_PATH}\n')
            f.write(f'sys.path: {sys.path}\n\n')
            f.write(traceback.format_exc())
            f.write(f'{"="*80}\n\n')
    except:
        pass
    raise
