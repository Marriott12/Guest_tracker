# cPanel Deployment Guide for Guest Tracker

## Troubleshooting Common Deployment Issues

### Issue 1: "fatal: not a git repository"

**Problem:** The directory on cPanel doesn't have git initialized.

**Solutions:**

#### Option A: Initialize Git Repository (Recommended)
```bash
cd ~/public_html/guest_tracker
git init
git remote add origin https://github.com/Marriott12/Guest_tracker.git
git fetch origin
git checkout main
git pull origin main
```

#### Option B: Clone Fresh Repository
```bash
cd ~/public_html
# Backup existing files if needed
mv guest_tracker guest_tracker_backup
# Clone repository
git clone https://github.com/Marriott12/Guest_tracker.git guest_tracker
cd guest_tracker
```

---

### Issue 2: Virtual Environment Not Found

**Problem:** Virtual environment path doesn't exist or is in a different location.

**Solutions:**

#### Step 1: Find Python Executable
```bash
# Check which Python versions are available
which python3
which python3.11
ls /usr/bin/python*
```

#### Step 2: Check Existing Virtual Environments
```bash
# List virtual environments in cPanel
ls -la ~/virtualenv/
ls -la ~/virtualenv/public_html/
```

#### Step 3: Create Virtual Environment via cPanel

**Using cPanel Interface (RECOMMENDED):**
1. Log into cPanel
2. Go to "Setup Python App" or "Python Selector"
3. Click "Create Application"
4. Fill in details:
   - **Python version:** 3.11
   - **Application root:** `public_html/guest_tracker`
   - **Application URL:** Your domain/subdomain
   - **Application startup file:** `guest_tracker/wsgi.py`
   - **Application Entry point:** `application`
5. Click "Create"
6. Copy the activation command shown (it will look like):
   ```bash
   source /home/envithcy/virtualenv/public_html/guest_tracker/3.11/bin/activate
   ```

**Manual Creation (if cPanel UI not available):**
```bash
# Find Python 3.11
which python3.11

# Create virtual environment
python3.11 -m venv ~/public_html/guest_tracker/.venv

# Activate it
source ~/public_html/guest_tracker/.venv/bin/activate
```

---

### Issue 3: Python/Pip Commands Not Found

**Problem:** Python commands aren't in PATH or virtual environment isn't activated.

**Solutions:**

#### If Virtual Environment Exists:
```bash
# Activate the virtual environment first
source ~/virtualenv/public_html/guest_tracker/3.11/bin/activate

# OR if you created .venv manually:
source ~/public_html/guest_tracker/.venv/bin/activate

# Now Python and pip should work
python --version
pip --version
```

#### If Virtual Environment Doesn't Exist:
```bash
# Use system Python directly to create venv
python3.11 -m venv ~/public_html/guest_tracker/.venv
source ~/public_html/guest_tracker/.venv/bin/activate
pip install --upgrade pip
```

---

## Complete Deployment Steps

### Step 1: Setup Git Repository

```bash
# Navigate to your application directory
cd ~/public_html/guest_tracker

# Check if git is initialized
ls -la .git

# If not, initialize it
git init
git remote add origin https://github.com/Marriott12/Guest_tracker.git
git fetch origin
git checkout -b main
git pull origin main
```

### Step 2: Create/Activate Virtual Environment

**Option A - Using cPanel Interface:**
1. Setup Python App in cPanel (as described above)
2. Note the activation command provided
3. Use that command in SSH

**Option B - Using SSH:**
```bash
cd ~/public_html/guest_tracker

# Create virtual environment
python3.11 -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
# Make sure virtual environment is activated
# You should see (.venv) or (3.11) in your prompt

cd ~/public_html/guest_tracker
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add the following (replace with your actual values):
```env
# Django Settings
SECRET_KEY=your-production-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server219.web-hosting.com

# Database Configuration (cPanel MySQL)
DB_ENGINE=django.db.backends.mysql
DB_NAME=envithcy_guesttracker
DB_USER=envithcy_guestuser
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@zambiaarmyevents.com

# reCAPTCHA Keys
RECAPTCHA_PUBLIC_KEY=your-recaptcha-site-key
RECAPTCHA_PRIVATE_KEY=your-recaptcha-secret-key

# Security Settings (for production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Time Zone
TIME_ZONE=Africa/Lusaka

# Static and Media Files
STATIC_ROOT=/home/envithcy/public_html/guest_tracker/staticfiles
MEDIA_ROOT=/home/envithcy/public_html/guest_tracker/media
STATIC_URL=/static/
MEDIA_URL=/media/
```

Save with `Ctrl+O`, `Enter`, then `Ctrl+X`

### Step 5: Install MySQL Client (if needed)

```bash
# Activate virtual environment first
source .venv/bin/activate

# Install MySQL client
pip install mysqlclient
```

If mysqlclient installation fails, try:
```bash
pip install pymysql
```

Then add to `guest_tracker/__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### Step 6: Run Migrations

```bash
# Make sure virtual environment is activated
cd ~/public_html/guest_tracker
python manage.py migrate
```

### Step 7: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 8: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 9: Configure Passenger/WSGI

Create or update `passenger_wsgi.py` in your application root:

```python
import os
import sys

# Add your project directory to the sys.path
project_home = '/home/envithcy/public_html/guest_tracker'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'guest_tracker.settings'

# Activate virtual environment
virtualenv = '/home/envithcy/public_html/guest_tracker/.venv'
activate_this = os.path.join(virtualenv, 'bin', 'activate_this.py')

# For Python 3.11+, activate_this.py might not exist
# Instead, we update sys.path
sys.path.insert(0, os.path.join(virtualenv, 'lib', 'python3.11', 'site-packages'))

# Import Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Step 10: Set File Permissions

```bash
cd ~/public_html/guest_tracker
chmod -R 755 .
chmod 644 .env
chmod 644 db.sqlite3  # if using SQLite
chmod -R 755 media/
chmod -R 755 staticfiles/
```

### Step 11: Restart Application

**In cPanel:**
1. Go to "Setup Python App"
2. Find your application
3. Click "Restart"

**Or via SSH:**
```bash
touch ~/public_html/guest_tracker/passenger_wsgi.py
```

---

## Verification Checklist

After deployment, verify:

- [ ] Website loads without errors
- [ ] Static files (CSS, JS) are loading
- [ ] Admin interface is accessible at `/admin/`
- [ ] Guest registration form shows reCAPTCHA
- [ ] Login form shows reCAPTCHA
- [ ] Email sending works (test by adding a guest with "Send Invitation")
- [ ] Database connections work
- [ ] File uploads work (if applicable)

---

## Common Issues and Solutions

### 1. "DisallowedHost" Error

**Problem:** Domain not in ALLOWED_HOSTS

**Solution:**
```bash
nano .env
# Add all your domains to ALLOWED_HOSTS
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server219.web-hosting.com,*.yourdomain.com
```

### 2. Static Files Not Loading (404 errors)

**Problem:** Static files not collected or wrong path

**Solution:**
```bash
python manage.py collectstatic --noinput
# Check STATIC_ROOT in .env matches your server path
```

### 3. "ImproperlyConfigured: mysqlclient" Error

**Problem:** MySQL Python adapter not installed

**Solution:**
```bash
pip install mysqlclient
# Or if that fails:
pip install pymysql
```

### 4. Permission Denied Errors

**Problem:** Wrong file permissions

**Solution:**
```bash
chmod -R 755 ~/public_html/guest_tracker
chown -R envithcy:envithcy ~/public_html/guest_tracker
```

### 5. "ModuleNotFoundError" After Deployment

**Problem:** Dependencies not installed in virtual environment

**Solution:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Database Setup in cPanel

### Create MySQL Database:

1. **In cPanel → MySQL Databases:**
   - Create database: `envithcy_guesttracker`
   - Create user: `envithcy_guestuser`
   - Set strong password
   - Add user to database with ALL PRIVILEGES

2. **Note these details for .env:**
   - DB_NAME=envithcy_guesttracker
   - DB_USER=envithcy_guestuser
   - DB_PASSWORD=(password you set)
   - DB_HOST=localhost
   - DB_PORT=3306

---

## Email Setup in cPanel

### Option 1: cPanel Email Account

1. Create email account in cPanel: `noreply@yourdomain.com`
2. Use these settings in .env:
   ```env
   EMAIL_HOST=mail.yourdomain.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=noreply@yourdomain.com
   EMAIL_HOST_PASSWORD=your_email_password
   ```

### Option 2: Gmail SMTP

1. Enable 2FA on Gmail
2. Generate App Password
3. Use these settings:
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

---

## Quick Commands Reference

```bash
# Navigate to project
cd ~/public_html/guest_tracker

# Activate virtual environment
source .venv/bin/activate

# Pull latest changes
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Check for errors
python manage.py check --deploy

# Restart application
touch passenger_wsgi.py
```

---

## Need More Help?

### Check Logs:

**Application Errors:**
```bash
tail -f ~/logs/passenger.log
tail -f ~/logs/error_log
```

**Django Debug:**
Temporarily set in .env:
```env
DEBUG=True
```
Then check browser for detailed error messages. **Remember to set back to False!**

### Contact Support:
- cPanel hosting support for server-specific issues
- Check Django documentation: https://docs.djangoproject.com/
- Check repository issues: https://github.com/Marriott12/Guest_tracker/issues

---

**Last Updated:** November 2025  
**Server:** server219.web-hosting.com  
**User:** envithcy
