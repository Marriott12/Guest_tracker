# 🚀 Quick Deployment Commands for cPanel

## Copy and paste these commands in your SSH terminal

### Step 1: Navigate to your project directory
```bash
cd ~/public_html/guest_tracker
```

---

### Step 2: Initialize Git Repository (First Time Only)
```bash
git init
git remote add origin https://github.com/Marriott12/Guest_tracker.git
git fetch origin
git checkout -b main
git pull origin main
```

---

### Step 3: Run the Automated Setup Script
```bash
chmod +x setup_cpanel.sh
./setup_cpanel.sh
```

The script will automatically:
- ✅ Check/pull git repository
- ✅ Find or create virtual environment
- ✅ Install all dependencies
- ✅ Run database migrations
- ✅ Collect static files
- ✅ Offer to create superuser

---

## OR Do It Manually (if script doesn't work)

### Step 1: Create Virtual Environment
```bash
cd ~/public_html/guest_tracker
python3.11 -m venv .venv
```

### Step 2: Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Step 3: Upgrade pip
```bash
pip install --upgrade pip
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment (.env file)
```bash
nano .env
```

**Add these settings (replace with your actual values):**
```env
SECRET_KEY=your-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server219.web-hosting.com

DB_ENGINE=django.db.backends.mysql
DB_NAME=envithcy_guesttracker
DB_USER=envithcy_guestuser
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@zambiaarmyevents.com

RECAPTCHA_PUBLIC_KEY=your-recaptcha-site-key
RECAPTCHA_PRIVATE_KEY=your-recaptcha-secret-key

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

TIME_ZONE=Africa/Lusaka

STATIC_ROOT=/home/envithcy/public_html/guest_tracker/staticfiles
MEDIA_ROOT=/home/envithcy/public_html/guest_tracker/media
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 6: Install MySQL Support
```bash
pip install mysqlclient
```

If that fails, use:
```bash
pip install pymysql
```

Then edit `guest_tracker/__init__.py` and add:
```bash
nano guest_tracker/__init__.py
```
Add these lines:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### Step 7: Run Migrations
```bash
python manage.py migrate
```

### Step 8: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 9: Create Superuser (Admin Account)
```bash
python manage.py createsuperuser
```

### Step 10: Update passenger_wsgi.py
```bash
nano passenger_wsgi.py
```

Change line 18 to your cPanel username:
```python
CPANEL_USER = 'envithcy'  # Your username here
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 11: Set Permissions
```bash
chmod -R 755 ~/public_html/guest_tracker
chmod 644 .env
chmod -R 755 media/
chmod -R 755 staticfiles/
```

### Step 12: Restart Application in cPanel

**Option A - Via cPanel Web Interface:**
1. Log into cPanel
2. Go to "Setup Python App"
3. Find your application
4. Click "Restart"

**Option B - Via SSH:**
```bash
touch ~/public_html/guest_tracker/passenger_wsgi.py
```

---

## 📋 Before Deployment Checklist

Make sure you have:

- [ ] Created MySQL database in cPanel:
  - Database name: `envithcy_guesttracker`
  - Database user: `envithcy_guestuser`
  - User has ALL PRIVILEGES on database

- [ ] Created email account in cPanel (if using cPanel email):
  - Email: `noreply@yourdomain.com`

- [ ] Obtained reCAPTCHA keys from Google:
  - Go to: https://www.google.com/recaptcha/admin
  - Create site with reCAPTCHA v2 Checkbox
  - Add your domain(s)

- [ ] Updated `.env` file with all production settings

---

## 🔍 Verification Commands

After deployment, run these to verify:

```bash
# Check if virtual environment is activated (should show (.venv) in prompt)
which python

# Check Python version
python --version

# Check Django installation
python -c "import django; print(django.get_version())"

# Check if all apps are installed
python manage.py check

# Check deployment configuration
python manage.py check --deploy

# List all migrations
python manage.py showmigrations

# Check database connection
python manage.py dbshell
# Type: SELECT 1; then \q to exit
```

---

## 🆘 Quick Troubleshooting

### If you see "command not found" errors:
```bash
# Make sure virtual environment is activated
source ~/public_html/guest_tracker/.venv/bin/activate

# OR if using cPanel's virtualenv:
source ~/virtualenv/public_html/guest_tracker/3.11/bin/activate
```

### If git pull fails:
```bash
# Check remote URL
git remote -v

# Re-add if needed
git remote set-url origin https://github.com/Marriott12/Guest_tracker.git
```

### If migrations fail:
```bash
# Check database connection
python manage.py dbshell

# If connection fails, verify .env database settings
nano .env
```

### If static files don't load:
```bash
# Re-collect static files
python manage.py collectstatic --clear --noinput

# Check STATIC_ROOT path
echo $STATIC_ROOT
ls -la staticfiles/
```

### View error logs:
```bash
tail -50 ~/logs/error_log
tail -50 ~/logs/passenger_error.log
```

---

## 📞 Getting Help

If issues persist, see the full troubleshooting guide:
```bash
cat CPANEL_DEPLOYMENT_GUIDE.md
```

Or check specific sections:
```bash
# For git issues
grep -A 20 "Issue 1: fatal: not a git repository" CPANEL_DEPLOYMENT_GUIDE.md

# For virtual environment issues
grep -A 30 "Issue 2: Virtual Environment Not Found" CPANEL_DEPLOYMENT_GUIDE.md

# For Python/pip issues
grep -A 20 "Issue 3: Python/Pip Commands Not Found" CPANEL_DEPLOYMENT_GUIDE.md
```

---

## 🔄 Future Updates

When you need to update the application later:

```bash
cd ~/public_html/guest_tracker
source .venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
touch passenger_wsgi.py  # Restarts the app
```

---

**Server:** server219.web-hosting.com  
**User:** envithcy  
**Project:** guest_tracker  
**Python:** 3.11  
**Framework:** Django 5.2.6
