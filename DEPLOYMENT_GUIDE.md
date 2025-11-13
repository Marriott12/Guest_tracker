# Guest Tracker Deployment Guide

This guide covers deploying the Guest Tracker application to cPanel hosting.

## Prerequisites

- Git repository: `Marriott12/Guest_tracker`
- cPanel hosting account
- Python 3.11+ support on cPanel
- Domain configured: `guests.envisagezm.com`

## Quick Deployment

### 1. Local Changes

```powershell
# Use the automated deployment script
.\quick_deploy.ps1
```

This script will:
- Check for uncommitted changes
- Prompt for commit message
- Push changes to GitHub
- Display SSH connection instructions

### 2. Server Deployment

SSH into your cPanel server:
```bash
ssh envithcy@server219.web-hosting.com
```

Navigate to project and pull changes:
```bash
cd ~/public_html/guest_tracker
git pull origin main
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate
pip install -r requirements_clean.txt
python manage.py migrate
python manage.py collectstatic --noinput
touch ~/public_html/guest_tracker/tmp/restart.txt
```

## Environment Configuration

### Production .env File

Create/update `.env` on the server with:

```env
# Security
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=guests.envisagezm.com,www.envisagezm.com

# Database (MySQL)
DB_ENGINE=django.db.backends.mysql
DB_NAME=envithcy_guesttracker
DB_USER=envithcy_guestuser
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.envisagezm.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@envisagezm.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@envisagezm.com

# reCAPTCHA (v2 Checkbox)
RECAPTCHA_PUBLIC_KEY=your-site-key
RECAPTCHA_PRIVATE_KEY=your-secret-key

# Security Headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

## reCAPTCHA Setup

The application uses reCAPTCHA v2 Checkbox. Setup instructions are in `RECAPTCHA_SETUP.md`.

**IMPORTANT**: Do NOT use reCAPTCHA Enterprise keys - they are incompatible with django-recaptcha 3.0.0.

## Verification

After deployment, verify:

1. Visit https://guests.envisagezm.com
2. Check that landing page loads
3. Test login functionality
4. Test reCAPTCHA on forms
5. Verify static files load correctly

Monitor logs:
```bash
tail -f ~/public_html/guest_tracker/logs/django.log
```

## Troubleshooting

### Static files not loading
```bash
python manage.py collectstatic --noinput --clear
```

### Database errors
Check database credentials in `.env` and ensure database exists:
```bash
mysql -u envithcy_guestuser -p envithcy_guesttracker
```

### Application not restarting
```bash
touch ~/public_html/guest_tracker/tmp/restart.txt
# Or
mkdir -p ~/public_html/guest_tracker/tmp
touch ~/public_html/guest_tracker/tmp/restart.txt
```

## Support Files

- `quick_deploy.ps1` - Automated local deployment script
- `passenger_wsgi.py` - WSGI configuration for cPanel
- `requirements_clean.txt` - Python dependencies
- `.env.example` - Environment template

For security best practices, see `SECURITY.md`.
For user portal documentation, see `GUEST_PORTAL_GUIDE.md`.
